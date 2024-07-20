import os
import json
import boto3
import subprocess
import time
import chardet
import logging
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError


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
        return "", "unknown error while running the scan for the ip: {ip} with description:\n{e}"


def main():
    setup_logging()

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
    except (NoCredentialsError, PartialCredentialsError):
        logging.error('Error: AWS credentials not found or incomplete.')
    except ClientError as e:
        logging.error(f'Unexpected error: {e}')
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

            logging.info("Scan result: %s", stdout)
            if stderr:
                logging.error("Scan error: %s", stderr)
            else:
                delete_message_from_sqs(queue_url, receipt_handle)
                logging.info("deleted message from sqs: %s", ip)

        time.sleep(scan_interval)


if __name__ == "__main__":
    main()
