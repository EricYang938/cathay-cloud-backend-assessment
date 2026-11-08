"""Real HTTP → production handler → boto3 → Moto HTTP emulator. Not AWS deployment evidence."""

import os
import subprocess
import sys
import time

import boto3
import pytest
import requests

from scripts.smoke_test import run


def wait(url, process):
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError("Local dependency exited")
        try:
            requests.get(url, timeout=0.2)
            return
        except requests.RequestException:
            time.sleep(0.1)
    raise RuntimeError("Local dependency did not start")


@pytest.fixture
def http_stack(monkeypatch):
    # Ports fixed intentionally: tests are serial. No cloud credentials or real endpoints.
    env = {
        **os.environ,
        "DYNAMODB_ENDPOINT_URL": "http://127.0.0.1:18000",
        "TABLE_NAME": "integration-tasks",
    }
    monkeypatch.setenv("DYNAMODB_ENDPOINT_URL", env["DYNAMODB_ENDPOINT_URL"])
    moto = subprocess.Popen(
        [sys.executable, "-m", "moto.server", "-H", "127.0.0.1", "-p", "18000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    api = None
    try:
        wait("http://127.0.0.1:18000", moto)
        table = boto3.resource("dynamodb", endpoint_url=env["DYNAMODB_ENDPOINT_URL"]).create_table(
            TableName=env["TABLE_NAME"],
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[{"AttributeName": "task_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "task_id", "AttributeType": "S"}],
        )
        api = subprocess.Popen(
            [sys.executable, "-m", "scripts.dev_server"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        wait("http://127.0.0.1:8001/health", api)
        yield "http://127.0.0.1:8001", table
    finally:
        for proc in (api, moto):
            if proc:
                proc.terminate()
                proc.wait(timeout=10)


def test_http_crud(http_stack):
    url, _ = http_stack
    run(url, os.environ["DEMO_TOKEN"])


def test_separate_client_reads_persisted_item(http_stack):
    url, table = http_stack
    headers = {"Authorization": "Bearer " + os.environ["DEMO_TOKEN"]}
    created = requests.post(
        url + "/tasks", headers=headers, json={"title": "Persistence proof"}, timeout=5
    ).json()
    # Independent SDK client directly reads the item stored by the HTTP API subprocess.
    record = table.get_item(Key={"task_id": created["task_id"]}, ConsistentRead=True)["Item"]
    assert record == created
    assert (
        requests.delete(
            url + "/tasks/" + created["task_id"], headers=headers, timeout=5
        ).status_code
        == 204
    )
