import json
import boto3
from config import AWS_REGION, SQS_QUEUE_URL

sqs = boto3.client("sqs", region_name=AWS_REGION)


def send_completion_notification(task):
    message = {
        "event": "task_completed",
        "task_id": task["id"],
        "title": task["title"],
    }
    sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps(message),
    )