import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from src.utils.errors import MissingTask


class DynamoRepository:
    def __init__(self, table):
        self.table = table

    def create(self, item):
        self.table.put_item(Item=item, ConditionExpression="attribute_not_exists(task_id)")
        return item

    def get(self, task_id):
        item = self.table.get_item(Key={"task_id": task_id}, ConsistentRead=True).get("Item")
        if not item:
            raise MissingTask()
        return item

    def list(self, limit=50, cursor=None):
        args = {"Limit": limit, "ConsistentRead": True}
        if cursor:
            args["ExclusiveStartKey"] = {"task_id": cursor}
        result = self.table.scan(**args)
        return {
            "items": result.get("Items", []),
            "next_cursor": result.get("LastEvaluatedKey", {}).get("task_id"),
        }

    def update(self, task_id, changes):
        # Atomic update: no read/replace race and no accidental resurrection after delete.
        names = {f"#f{i}": k for i, k in enumerate(changes)}
        values = {f":v{i}": v for i, v in enumerate(changes.values())}
        expression = "SET " + ", ".join(f"#f{i} = :v{i}" for i in range(len(changes)))
        try:
            result = self.table.update_item(
                Key={"task_id": task_id},
                UpdateExpression=expression,
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
                ConditionExpression="attribute_exists(task_id)",
                ReturnValues="ALL_NEW",
            )
            return result["Attributes"]
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise MissingTask() from None
            raise

    def delete(self, task_id):
        try:
            self.table.delete_item(
                Key={"task_id": task_id}, ConditionExpression="attribute_exists(task_id)"
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise MissingTask() from None
            raise


def build_repository():
    endpoint = os.environ.get("DYNAMODB_ENDPOINT_URL")
    if endpoint and os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        raise RuntimeError("Local endpoint is prohibited in Lambda")
    db = boto3.resource(
        "dynamodb",
        endpoint_url=endpoint,
        config=Config(
            connect_timeout=2, read_timeout=3, retries={"max_attempts": 1, "mode": "standard"}
        ),
    )
    return DynamoRepository(db.Table(os.environ["TABLE_NAME"]))
