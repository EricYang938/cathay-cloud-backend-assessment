"""Start a loopback-only, disposable demo without AWS, Docker or manual credentials."""

import os
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path

import boto3
import requests

ROOT = Path(__file__).resolve().parents[1]


def demo_environment():
    env = {**os.environ}
    for key in (
        "AWS_PROFILE",
        "AWS_DEFAULT_PROFILE",
        "AWS_SESSION_TOKEN",
        "AWS_LAMBDA_FUNCTION_NAME",
    ):
        env.pop(key, None)
    env.update(
        {
            "AWS_ACCESS_KEY_ID": "testing",
            "AWS_SECRET_ACCESS_KEY": "testing",
            "AWS_DEFAULT_REGION": "ap-northeast-1",
            "AWS_EC2_METADATA_DISABLED": "true",
            "DYNAMODB_ENDPOINT_URL": "http://127.0.0.1:18000",
            "TABLE_NAME": "demo-tasks",
            "ALLOWED_ORIGIN": "http://localhost:8080",
            "DEMO_TOKEN": secrets.token_urlsafe(32),
        }
    )
    return env


def wait_ready(url, process):
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError("A local service exited before it was ready")
        try:
            response = requests.get(url, timeout=0.3)
            if response.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(0.1)
    raise RuntimeError("Local service startup timed out")


def main():
    # Refuse occupied ports instead of accidentally sending credentials to another service.
    for port in (18000, 8001, 8080):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                raise SystemExit(
                    f"Port {port} is in use. Stop the existing service first."
                ) from None
    env = demo_environment()
    for key in (
        "AWS_PROFILE",
        "AWS_DEFAULT_PROFILE",
        "AWS_SESSION_TOKEN",
        "AWS_LAMBDA_FUNCTION_NAME",
    ):
        os.environ.pop(key, None)
    state = ROOT / "local-state"
    state.mkdir(exist_ok=True)
    token_file = state / "demo-token.txt"
    with token_file.open("w", encoding="utf-8") as handle:
        os.chmod(token_file, 0o600)
        handle.write(env["DEMO_TOKEN"])
    processes = []
    try:

        def launch(args, url):
            process = subprocess.Popen(
                [sys.executable, *args],
                cwd=ROOT,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            processes.append(process)
            wait_ready(url, process)

        launch(["-m", "moto.server", "-H", "127.0.0.1", "-p", "18000"], "http://127.0.0.1:18000")
        db = boto3.resource(
            "dynamodb",
            endpoint_url=env["DYNAMODB_ENDPOINT_URL"],
            region_name=env["AWS_DEFAULT_REGION"],
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
        )
        db.create_table(
            TableName=env["TABLE_NAME"],
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[{"AttributeName": "task_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "task_id", "AttributeType": "S"}],
        )
        launch(["-m", "scripts.dev_server"], "http://127.0.0.1:8001/health")
        launch(
            ["-m", "http.server", "8080", "--bind", "127.0.0.1", "--directory", "frontend"],
            "http://localhost:8080",
        )
        print("Demo ready: http://localhost:8080", flush=True)
        print("API: http://127.0.0.1:8001", flush=True)
        print("Copy the token from local-state/demo-token.txt into the frontend.", flush=True)
        print(
            "Moto is a local emulator: tasks disappear after shutdown. Ctrl+C to stop.", flush=True
        )
        while all(process.poll() is None for process in processes):
            time.sleep(0.5)
        raise RuntimeError("A local service stopped unexpectedly")
    except KeyboardInterrupt:
        print("Stopping local demo.", flush=True)
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=10)
        token_file.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
