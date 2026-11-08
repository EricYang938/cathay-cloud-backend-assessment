import os

import boto3
from botocore.exceptions import ClientError


def main():
    endpoint = os.environ.get("DYNAMODB_ENDPOINT_URL", "")
    if not endpoint.startswith(("http://127.0.0.1:", "http://localhost:", "http://dynamodb:")):
        raise SystemExit("Only a local DynamoDB endpoint is accepted")
    client = boto3.client("dynamodb", endpoint_url=endpoint)
    table = os.environ.get("TABLE_NAME", "local-tasks")
    try:
        client.create_table(
            TableName=table,
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[{"AttributeName": "task_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "task_id", "AttributeType": "S"}],
        )
        client.get_waiter("table_exists").wait(TableName=table)
        print("Local table ready:", table)
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ResourceInUseException":
            raise
        print("Local table already exists:", table)


if __name__ == "__main__":
    main()
