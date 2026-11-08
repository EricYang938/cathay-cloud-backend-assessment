import re

from src.models.validation import body, invalid, task_id
from src.services.tasks import TaskService
from src.utils.errors import ApiError


def route(event, repository_factory, weather):
    method = event["requestContext"]["http"]["method"].upper()
    path = event.get("rawPath", "/")
    query = event.get("queryStringParameters") or {}
    if path == "/health":
        if method != "GET":
            raise ApiError(405, "METHOD_NOT_ALLOWED", "Method not allowed")
        return 200, {"status": "ok", "service": "cloud-tasks"}
    if path == "/weather":
        if method != "GET":
            raise ApiError(405, "METHOD_NOT_ALLOWED", "Method not allowed")
        return 200, weather.query(query.get("city", ""))
    match = re.fullmatch(r"/tasks/([^/]+)", path)
    if path != "/tasks" and not match:
        raise ApiError(404, "NOT_FOUND", "Route not found")
    allowed = ("GET", "POST") if not match else ("GET", "PATCH", "DELETE")
    if method not in allowed:
        raise ApiError(405, "METHOD_NOT_ALLOWED", "Method not allowed")
    identifier = task_id(match[1]) if match else None
    # Validate request before opening a dependency connection.
    data = body(event) if method in ("POST", "PATCH") else None
    if method == "GET" and not match:
        try:
            limit = int(query.get("limit", "50"))
        except (ValueError, TypeError):
            invalid("Limit must be an integer")
        if not 1 <= limit <= 100:
            invalid("Limit must be between 1 and 100")
        cursor = task_id(query["cursor"]) if query.get("cursor") else None
    repo = repository_factory()
    service = TaskService(repo)
    if path == "/tasks":
        if method == "POST":
            return 201, service.create(data)
        return 200, repo.list(limit, cursor)
    if method == "GET":
        return 200, repo.get(identifier)
    if method == "PATCH":
        return 200, service.update(identifier, data)
    repo.delete(identifier)
    return 204, None
