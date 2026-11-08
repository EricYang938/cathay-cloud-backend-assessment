import base64
import json
from unittest.mock import Mock
from uuid import uuid4

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from src.app import make_handler
from src.models.validation import task_id
from src.repositories.dynamodb import DynamoRepository, build_repository
from src.services.tasks import TaskService
from src.utils.errors import ApiError


def test_crud(call):
    code, item = call("POST", data={"title": "  Demo  "})
    assert code == 201 and item["title"] == "Demo" and item["status"] == "TODO"
    path = "/tasks/" + item["task_id"]
    assert item["created_at"].endswith("Z")
    assert call("GET", path)[1] == item
    code, updated = call("PATCH", path, {"status": "DONE", "description": "ok"})
    assert code == 200 and updated["status"] == "DONE"
    assert updated["created_at"] == item["created_at"]
    assert call("GET")[1]["items"] == [updated]
    assert call("DELETE", path) == (204, None)
    assert call("GET", path)[0] == 404
    assert call("PATCH", path, {"title": "Gone"})[0] == 404
    assert call("DELETE", path)[0] == 404


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"title": " "},
        {"title": None},
        {"title": 1},
        {"title": "x" * 201},
        {"title": "ok", "status": "bad"},
        {"title": "ok", "status": []},
        {"title": "ok", "extra": 1},
        {"title": "ok", "description": "x" * 2001},
        {"title": "ok", "description": None},
    ],
)
def test_invalid_create(call, data):
    assert call("POST", data=data)[0] == 400


@pytest.mark.parametrize("raw", ["{", "[]", "null", '"string"', "", '{"title": NaN}'])
def test_bad_json(call, raw):
    assert call("POST", raw=raw)[0] == 400


@pytest.mark.parametrize(
    "method,path,code",
    [
        ("GET", "/tasks/" + str(uuid4()), 404),
        ("GET", "/tasks/no", 400),
        ("PUT", "/tasks", 405),
        ("POST", "/weather", 405),
        ("DELETE", "/health", 405),
        ("GET", "/nope", 404),
    ],
)
def test_routing(call, method, path, code):
    assert call(method, path)[0] == code


@pytest.mark.parametrize(
    "raw",
    [
        '{"title":"ok","description":NaN}',
        '{"title":"ok","description":Infinity}',
        '{"title":"first","title":"second"}',
    ],
)
def test_strict_json(call, raw):
    assert call("POST", raw=raw)[0] == 400


def test_patch_empty(call):
    item = call("POST", data={"title": "ok"})[1]
    assert call("PATCH", "/tasks/" + item["task_id"], {})[0] == 400


def test_body_limit(call):
    assert call("POST", raw='{"title":"' + "x" * 20000 + '"}')[0] == 413


@pytest.mark.parametrize("limit", ["0", "101", "foo", "1.1"])
def test_bad_limit(call, limit):
    assert call(query={"limit": limit})[0] == 400


def test_pagination(call):
    for i in range(5):
        call("POST", data={"title": str(i)})
    ids, cursor = set(), None
    while True:
        query = {"limit": "2", **({"cursor": cursor} if cursor else {})}
        code, page = call(query=query)
        assert code == 200
        ids.update(i["task_id"] for i in page["items"])
        cursor = page["next_cursor"]
        if not cursor:
            break
    assert len(ids) == 5


@pytest.mark.parametrize(
    "exception,code",
    [
        (
            ClientError(
                {"Error": {"Code": "AccessDeniedException", "Message": "SECRET"}}, "GetItem"
            ),
            503,
        ),
        (EndpointConnectionError(endpoint_url="SECRET"), 503),
        (RuntimeError("SECRET"), 500),
    ],
)
def test_safe_errors(exception, code, monkeypatch):
    repo = Mock()
    repo.list.side_effect = exception
    handler = make_handler(lambda: repo)
    import os

    response = handler(
        {
            "rawPath": "/tasks",
            "headers": {"authorization": "Bearer " + os.environ["DEMO_TOKEN"]},
            "requestContext": {"http": {"method": "GET"}},
        },
        None,
    )
    assert response["statusCode"] == code and "SECRET" not in response["body"]


def test_auth_and_cors(handler, monkeypatch):
    event = {"rawPath": "/tasks", "headers": {}, "requestContext": {"http": {"method": "GET"}}}
    assert handler(event, None)["statusCode"] == 401
    event["rawPath"] = "/health"
    assert handler(event, None)["statusCode"] == 200
    event["requestContext"]["http"]["method"] = "OPTIONS"
    event["headers"] = {"origin": "https://evil.example"}
    response = handler(event, None)
    assert response["statusCode"] == 403
    assert "access-control-allow-origin" not in response["headers"]
    event["headers"]["origin"] = "http://localhost:8080"
    assert handler(event, None)["statusCode"] == 204
    event["requestContext"]["http"]["method"] = "GET"
    event["rawPath"] = "/tasks"
    monkeypatch.delenv("DEMO_TOKEN")
    assert handler(event, None)["statusCode"] == 503


def test_base64(handler):
    import os

    event = {
        "rawPath": "/tasks",
        "headers": {"authorization": "Bearer " + os.environ["DEMO_TOKEN"]},
        "requestContext": {"http": {"method": "POST"}},
        "isBase64Encoded": True,
        "body": base64.b64encode(json.dumps({"title": "中文"}).encode()).decode(),
    }
    assert handler(event, None)["statusCode"] == 201
    event["body"] = "@@@"
    assert handler(event, None)["statusCode"] == 400


def test_fake_repository_injection():
    repo = Mock()
    TaskService(repo).create({"title": "No AWS needed"})
    assert repo.create.call_args.args[0]["title"] == "No AWS needed"


def test_repository_errors_propagate():
    table = Mock()
    table.update_item.side_effect = ClientError({"Error": {"Code": "AccessDenied"}}, "UpdateItem")
    table.delete_item.side_effect = ClientError({"Error": {"Code": "AccessDenied"}}, "DeleteItem")
    repo = DynamoRepository(table)
    with pytest.raises(ClientError):
        repo.update(str(uuid4()), {"status": "DONE"})
    with pytest.raises(ClientError):
        repo.delete(str(uuid4()))


def test_no_local_endpoint_in_cloud(monkeypatch):
    monkeypatch.setenv("DYNAMODB_ENDPOINT_URL", "http://localhost:8000")
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "demo")
    with pytest.raises(RuntimeError):
        build_repository()


@pytest.mark.parametrize("value", [None, 123, "INVALID", str(uuid4()).upper()])
def test_invalid_ids(value):
    with pytest.raises(ApiError):
        task_id(value)
