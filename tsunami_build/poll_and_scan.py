import os
import json
import re

import boto3
import subprocess
import time
import chardet
import logging
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from prometheus_client import start_http_server, Gauge


# Define Prometheus metrics
classpath_scan_time_gauge = Gauge('classpath_scan_time', 'Time taken for classpath scan', ['ip'])
nmap_scan_time_gauge = Gauge('nmap_scan_time', 'Time taken for nmap scan', ['ip'])
port_scanning_time_gauge = Gauge('port_scanning_time', 'Time taken for port scanning', ['ip'])
service_fingerprinting_time_gauge = Gauge('service_fingerprinting_time', 'Time taken for service fingerprinting', ['ip'])
service_fingerprinting_plugins_gauge = Gauge('service_fingerprinting_plugins', 'Number of plugins used for service fingerprinting', ['ip'])
vuln_detection_time_gauge = Gauge('vuln_detection_time', 'Time taken for vulnerability detection', ['ip'])
vuln_detection_plugins_gauge = Gauge('vuln_detection_plugins', 'Number of plugins used for vulnerability detection', ['ip'])
failed_run = Gauge('failed_run', 'Number of failed scans', ['ip'])


def extract_values(text):
    values = {}

    # Define regex patterns
    patterns = {
        'classpath_scan': r'Full classpath scan took ([\d.]+) min',
        'nmap_scan': r'Finished nmap scan on target .* in ([\d.]+) min',
        'port_scanning': r'Port scanning phase \(([\d.]+) min\)',
        'service_fingerprinting': r'Service fingerprinting phase \(([\d.]+) ms\) with (\d+) plugin\(s\)',
        'vuln_detection': r'Vuln detection phase \(([\d.]+) ms\) with (\d+) plugin\(s\)',
    }

    # Extract values using regex
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            values[key] = match.groups()
    classpath_scan_time = float(values.get('classpath_scan', [0])[0])
    nmap_scan_time = float(values.get('nmap_scan', [0])[0])
    port_scanning_time = float(values.get('port_scanning', [0])[0])
    service_fingerprinting_time = float(values.get('service_fingerprinting', [0])[0])
    service_fingerprinting_plugins = int(values.get('service_fingerprinting', [0, 0])[1])
    vuln_detection_time = float(values.get('vuln_detection', [0])[0])
    vuln_detection_plugins = int(values.get('vuln_detection', [0, 0])[1])
    return {
        'classpath_scan_time': classpath_scan_time,
        'port_scanning_time': port_scanning_time,
        'nmap_scan_time': nmap_scan_time,
        'service_fingerprinting_time': service_fingerprinting_time,
        'service_fingerprinting_plugins': service_fingerprinting_plugins,
        'vuln_detection_time': vuln_detection_time,
        'vuln_detection_plugins': vuln_detection_plugins,
    }

def setup_logging():
    log_dir = '/logs'
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'tsunami_scanner.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def get_messages_from_sqs(queue_url, batch_size):
    sqs_client = boto3.client('sqs')
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=batch_size,
        WaitTimeSeconds=20,
        VisibilityTimeout=600
    )
    return response.get('Messages', [])

def delete_message_from_sqs(queue_url, receipt_handle):
    sqs_client = boto3.client('sqs')
    sqs_client.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )

def run_tsunami_scan(ip):
    try:
        result = subprocess.run(
            ["java", "-cp", "tsunami.jar:plugins/*", "-Dtsunami-config.location=tsunami_configuration.yaml",
             "com.google.tsunami.main.cli.TsunamiCli", '--ip-v4-target', ip],
            capture_output=True,
            text=True
        )
        logging.info(f"stdout: {result.stdout}")
        logging.info(f"stderr: {result.stderr}")
        return result.stdout, result.stderr
    except Exception as e:
        logging.exception(f"unknown error while running the scan for the ip: {ip} with description:\n{e}")
        return "", f"unknown error while running the scan for the ip: {ip} with description:\n{e}"

def export_metrics(values, ip):
    classpath_scan_time_gauge.labels(ip=ip).set(values['classpath_scan_time'])
    nmap_scan_time_gauge.labels(ip=ip).set(values['nmap_scan_time'])
    port_scanning_time_gauge.labels(ip=ip).set(values['port_scanning_time'])
    service_fingerprinting_time_gauge.labels(ip=ip).set(values['service_fingerprinting_time'])
    service_fingerprinting_plugins_gauge.labels(ip=ip).set(values['service_fingerprinting_plugins'])
    vuln_detection_time_gauge.labels(ip=ip).set(values['vuln_detection_time'])
    vuln_detection_plugins_gauge.labels(ip=ip).set(values['vuln_detection_plugins'])
    failed_run.labels(ip=ip).set(values['failed_run'])

def main():
    setup_logging()
    start_http_server(8000)

    session = boto3.Session(region_name='us-west-2')
    sqs = session.client('sqs')
    queue_name = 'tsunami_ip_list_queue'
    try:
        # Get the queue URL
        response = sqs.get_queue_url(QueueName=queue_name)
        queue_url = response['QueueUrl']
        logging.info(f'The URL for the queue "{queue_name}" is: {queue_url}')
    except sqs.exceptions.QueueDoesNotExist:
        logging.error(f'Error: The queue "{queue_name}" does not exist.')
        return
    except (NoCredentialsError, PartialCredentialsError):
        logging.error('Error: AWS credentials not found or incomplete.')
        return
    except ClientError as e:
        logging.error(f'Unexpected error: {e}')
        return
    batch_size = int(os.getenv('BATCH_SIZE', '5'))
    scan_interval = int(os.getenv('SCAN_INTERVAL', '30'))

    while True:
        messages = get_messages_from_sqs(queue_url, batch_size)

        if not messages:
            logging.info("No messages found")
            time.sleep(scan_interval)
            continue

        for message in messages:
            receipt_handle = message['ReceiptHandle']
            ip = message['Body']

            logging.info(f"Scanning IP: {ip}")
            stdout, stderr = run_tsunami_scan(ip)
            succ_values = {}
            logging.info("Scan result: %s", stdout)
            if stderr:
                logging.error("Scan error: %s", stderr)
                err_values = extract_values(stderr)
                err_values['failed_run'] = 1
                export_metrics(err_values, ip)
                logging.info(f"metrics to export: \n{err_values}")
            else:
                delete_message_from_sqs(queue_url, receipt_handle)
                logging.info("deleted message from sqs: %s", ip)
                succ_values ['failed_run'] = 0
                export_metrics(succ_values, ip)
                logging.info(f"metrics to export: \n{succ_values}")

        time.sleep(scan_interval)

if __name__ == "__main__":
    main()
