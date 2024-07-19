import os
import json
import boto3
import subprocess
import time
import chardet
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

def get_messages_from_sqs(queue_url, batch_size):
    sqs_client = boto3.client('sqs')
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=batch_size,
        WaitTimeSeconds=20
    )
    return response.get('Messages', [])

def delete_message_from_sqs(queue_url, receipt_handle):
    sqs_client = boto3.client('sqs')
    sqs_client.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )

def run_tsunami_scan(ip):
    result = subprocess.run(
        ["java", "-cp", "tsunami.jar:plugins/*", "-Dtsunami-config.location=tsunami.yaml", "com.google.tsunami.main.cli.TsunamiCli", '--ip-v4-target', ip],
        capture_output=True,
        text=True
    )
    return result.stdout, result.stderr

def main():
    with open('tf_output.json', 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
    tfvars ={}
    with open('tf_output.json', 'r', encoding=encoding) as file:
        for line in file:
            # Strip any leading/trailing whitespace and split by '='
            if '=' in line:
                key, value = line.strip().split('=', 1)
                key = key.strip()
                value = value.strip()
                tfvars[key] = value
    sqs = boto3.client('sqs')
    queue_name = 'tsunami_ip_list_queue'
    try:
        # Get the queue URL
        response = sqs.get_queue_url(QueueName=queue_name)
        queue_url = response['QueueUrl']
        print(f'The URL for the queue "{queue_name}" is: {queue_url}')
    except sqs.exceptions.QueueDoesNotExist:
        print(f'Error: The queue "{queue_name}" does not exist.')
    except (NoCredentialsError, PartialCredentialsError):
        print('Error: AWS credentials not found or incomplete.')
    except ClientError as e:
        print(f'Unexpected error: {e}')
    batch_size = int(os.getenv('BATCH_SIZE', '5'))
    scan_interval = int(os.getenv('SCAN_INTERVAL', '300'))

    while True:
        messages = get_messages_from_sqs(queue_url, batch_size)
        
        if not messages:
            print("No messages found")
            time.sleep(scan_interval)
            continue
        
        for message in messages:
            receipt_handle = message['ReceiptHandle']
            ip = message['Body']
            
            print(f"Scanning IP: {ip}")
            stdout, stderr = run_tsunami_scan(ip)
            
            print("Scan result:", stdout)
            if stderr:
                print("Scan error:", stderr)
            
            delete_message_from_sqs(queue_url, receipt_handle)
        
        time.sleep(scan_interval)

if __name__ == "__main__":
    main()

