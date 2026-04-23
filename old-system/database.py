import boto3
from config import AWS_REGION, DYNAMODB_TABLE

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)


def create_task(task):
    table.put_item(Item=task)
    return task


def get_all_tasks():
    response = table.scan()
    return response.get("Items", [])


def get_task(task_id):
    response = table.get_item(Key={"id": task_id})
    return response.get("Item")


def update_task(task_id, updates):
    expression_parts = []
    expression_values = {}
    for key, value in updates.items():
        expression_parts.append(f"#{key} = :{key}")
        expression_values[f":{key}"] = value

    expression_names = {f"#{k}": k for k in updates.keys()}

    response = table.update_item(
        Key={"id": task_id},
        UpdateExpression="SET " + ", ".join(expression_parts),
        ExpressionAttributeNames=expression_names,
        ExpressionAttributeValues=expression_values,
        ReturnValues="ALL_NEW",
    )
    return response.get("Attributes")


def delete_task(task_id):
    table.delete_item(Key={"id": task_id})