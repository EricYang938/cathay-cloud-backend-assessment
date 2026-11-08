"""Browser -> HTTP API -> boto3 -> Moto verification. Optional Playwright dependency."""

import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

import boto3
import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def wait(url, proc):
    for _ in range(100):
        if proc.poll() is not None:
            raise RuntimeError("Dependency exited")
        try:
            requests.get(url, timeout=0.2)
            return
        except requests.RequestException:
            time.sleep(0.1)
    raise RuntimeError("Dependency startup timeout")


def main():
    env = {
        **os.environ,
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_DEFAULT_REGION": "ap-northeast-1",
        "AWS_EC2_METADATA_DISABLED": "true",
        "DYNAMODB_ENDPOINT_URL": "http://127.0.0.1:18000",
        "TABLE_NAME": "ui-tasks",
        "ALLOWED_ORIGIN": "http://localhost:8080",
        "DEMO_TOKEN": secrets.token_urlsafe(32),
    }
    for key in (
        "AWS_PROFILE",
        "AWS_DEFAULT_PROFILE",
        "AWS_SESSION_TOKEN",
        "AWS_LAMBDA_FUNCTION_NAME",
    ):
        env.pop(key, None)
        os.environ.pop(key, None)
    processes = []
    checks = []
    shots = ROOT / "docs/screenshots"
    shots.mkdir(exist_ok=True)
    try:

        def launch(args, url):
            proc = subprocess.Popen(
                [sys.executable, *args],
                cwd=ROOT,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            processes.append(proc)
            wait(url, proc)

        launch(["-m", "moto.server", "-H", "127.0.0.1", "-p", "18000"], "http://127.0.0.1:18000")
        boto3.resource(
            "dynamodb",
            endpoint_url=env["DYNAMODB_ENDPOINT_URL"],
            region_name=env["AWS_DEFAULT_REGION"],
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
        ).create_table(
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
        with sync_playwright() as playwright:
            options = {"headless": True, "args": ["--no-sandbox"]}
            if os.environ.get("CHROMIUM_EXECUTABLE"):
                options["executable_path"] = os.environ["CHROMIUM_EXECUTABLE"]
            browser = playwright.chromium.launch(**options)
            page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto("http://localhost:8080")
            page.locator("#token").fill(env["DEMO_TOKEN"])
            page.locator("#connect").click()
            page.wait_for_function(
                "document.querySelector('#message').textContent.includes('已完成')"
            )
            checks.append("Connected frontend to actual local HTTP API")
            page.locator("#title").fill("完成雲端架構與 API 驗證")
            page.locator("#description").fill("Lambda、DynamoDB 與安全設計；逐項保留測試證據。")
            page.locator("#task-form button[type=submit]").click()
            page.locator(".task h3").filter(has_text="完成雲端架構與 API 驗證").wait_for()
            checks.append("Created and listed task through browser")
            page.locator(".task .edit").click()
            page.locator("#title").fill("完成雲端架構與 API 驗證（已審閱）")
            page.locator("#task-form button[type=submit]").click()
            page.locator(".task h3").filter(has_text="（已審閱）").wait_for()
            checks.append("Edited title through browser")
            page.wait_for_function("document.querySelector('#connect').disabled === false")
            page.locator(".task-controls select").select_option("DONE")
            page.wait_for_function(
                "document.querySelector('#message').textContent.includes('已完成')"
            )
            assert page.locator(".task-controls select").input_value() == "DONE"
            # Confirm persisted status from the independent HTTP client, not just the select value.
            persisted = requests.get(
                "http://127.0.0.1:8001/tasks",
                headers={"Authorization": "Bearer " + env["DEMO_TOKEN"]},
                timeout=5,
            ).json()
            assert persisted["items"][0]["status"] == "DONE"
            checks.append("Updated task status through browser and read it back via HTTP")
            page.locator("#title").fill("準備面試與技術選型說明")
            page.locator("#description").fill("釐清 Serverless 的取捨，整理未部署項目。")
            page.locator("#status").select_option("IN_PROGRESS")
            page.locator("#task-form button[type=submit]").click()
            page.wait_for_function("document.querySelectorAll('.task').length === 2")
            page.wait_for_function("document.querySelector('#connect').disabled === false")
            page.locator("#token").fill("")
            page.screenshot(path=str(shots / "desktop.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.screenshot(path=str(shots / "mobile.png"), full_page=True)
            checks.append("390px mobile viewport has no horizontal overflow")
            page.on("dialog", lambda dialog: dialog.accept())
            page.locator(".task .delete").first.click()
            page.wait_for_function("document.querySelectorAll('.task').length === 1")
            checks.append("Deleted task through browser")
            page.locator("#token").fill("invalid-demo-token")
            page.locator("#connect").click()
            page.wait_for_function("document.querySelector('#message').classList.contains('error')")
            assert "token" in page.locator("#message").inner_text().lower()
            assert page.locator(".task").count() == 0
            checks.append("Failed reconnect clears stale workspace data")
            checks.append("Rendered unauthorized error returned by real backend")
            assert not errors, errors
            checks.append("No browser JavaScript runtime errors")
            browser.close()
        report = {
            "status": "PASS",
            "scope": "Local frontend + real HTTP + Moto (not AWS)",
            "checks": checks,
        }
        (ROOT / "docs/evidence/frontend.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
    finally:
        for proc in reversed(processes):
            proc.terminate()
            proc.wait(timeout=10)


if __name__ == "__main__":
    main()
