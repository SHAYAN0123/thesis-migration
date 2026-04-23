import boto3
from config import AWS_REGION, S3_BUCKET

s3 = boto3.client("s3", region_name=AWS_REGION)


def upload_file(task_id, filename, file_data):
    key = f"{task_id}/{filename}"
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=file_data)
    url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
    return url


def list_files(task_id):
    prefix = f"{task_id}/"
    response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
    files = []
    for obj in response.get("Contents", []):
        url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{obj['Key']}"
        files.append(url)
    return files


def delete_files(task_id):
    prefix = f"{task_id}/"
    response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
    for obj in response.get("Contents", []):
        s3.delete_object(Bucket=S3_BUCKET, Key=obj["Key"])