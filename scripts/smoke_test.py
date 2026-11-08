"""HTTP CRUD smoke test; token is read only from environment, never printed."""

import argparse
import os

import requests


def run(base_url, token):
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    identifier = None
    try:
        response = session.post(
            base_url + "/tasks", json={"title": "Assessment smoke test"}, timeout=15
        )
        assert response.status_code == 201, f"POST status {response.status_code}"
        identifier = response.json()["task_id"]
        url = f"{base_url}/tasks/{identifier}"
        response = session.get(url, timeout=15)
        assert response.status_code == 200 and response.json()["status"] == "TODO"
        response = session.patch(url, json={"status": "DONE"}, timeout=15)
        assert response.status_code == 200 and response.json()["status"] == "DONE"
        response = session.get(url, timeout=15)
        assert response.status_code == 200 and response.json()["status"] == "DONE"
        assert session.delete(url, timeout=15).status_code == 204
        assert session.get(url, timeout=15).status_code == 404
        print("PASS: POST → GET → PATCH → GET → DELETE → GET 404")
    finally:
        if identifier:
            session.delete(f"{base_url}/tasks/{identifier}", timeout=15)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    args = parser.parse_args()
    run(args.base_url.rstrip("/"), os.environ["DEMO_TOKEN"])
