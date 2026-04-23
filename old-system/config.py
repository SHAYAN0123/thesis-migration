import os

AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "tasks")
S3_BUCKET = os.environ.get("S3_BUCKET", "task-attachments")
SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL", "https://sqs.eu-west-1.amazonaws.com/123456789/task-notifications")