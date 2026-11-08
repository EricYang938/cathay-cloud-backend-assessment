import json
import os
from unittest.mock import Mock

import boto3
import pytest
from moto import mock_aws

from src.app import make_handler
from src.repositories.dynamodb import DynamoRepository


@pytest.fixture(autouse=True)
def environment(monkeypatch):
    for name in (
        "AWS_PROFILE",
        "AWS_DEFAULT_PROFILE",
        "AWS_SESSION_TOKEN",
        "AWS_LAMBDA_FUNCTION_NAME",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-northeast-1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.setenv("DEMO_TOKEN", "unit-test-only-token-" + "x" * 32)
    monkeypatch.setenv("ALLOWED_ORIGIN", "http://localhost:8080")
    monkeypatch.delenv("DYNAMODB_ENDPOINT_URL", raising=False)


@pytest.fixture
def table():
    with mock_aws():
        db = boto3.resource("dynamodb")
        table = db.create_table(
            TableName="test-tasks",
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[{"AttributeName": "task_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "task_id", "AttributeType": "S"}],
        )
        yield table


@pytest.fixture
def repository(table):
    return DynamoRepository(table)


@pytest.fixture
def handler(repository):
    return make_handler(lambda: repository, Mock())


@pytest.fixture
def call(handler):
    def invoke(method="GET", path="/tasks", data=None, raw=None, headers=None, query=None):
        event = {
            "rawPath": path,
            "requestContext": {"http": {"method": method}},
            "headers": {"authorization": "Bearer " + os.environ["DEMO_TOKEN"], **(headers or {})},
            "queryStringParameters": query,
            "body": raw if raw is not None else json.dumps(data) if data is not None else "",
        }
        response = handler(event, None)
        return response["statusCode"], json.loads(response["body"]) if response["body"] else None

    return invoke
