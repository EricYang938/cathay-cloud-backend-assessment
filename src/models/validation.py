import base64
import binascii
import json
from uuid import UUID

from src.utils.errors import ApiError


def invalid(message):
    raise ApiError(400, "INVALID_INPUT", message)


def task_id(value):
    try:
        if str(UUID(value)) != value:
            invalid("Invalid task ID")
    except (ValueError, TypeError, AttributeError):
        invalid("Invalid task ID")
    return value


def reject_constant(_value):
    raise ValueError("Nonstandard JSON constant")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def body(event):
    raw = event.get("body") or ""
    try:
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(raw, validate=True).decode("utf-8")
        if len(raw.encode("utf-8")) > 16384:
            raise ApiError(413, "PAYLOAD_TOO_LARGE", "Request body exceeds 16 KiB")
        data = json.loads(raw, parse_constant=reject_constant, object_pairs_hook=unique_object)
    except (ValueError, UnicodeError, binascii.Error):
        invalid("Body must be valid UTF-8 JSON")
    if not isinstance(data, dict):
        invalid("Body must be a JSON object")
    return data


def fields(data, creating=False):
    if set(data) - {"title", "description", "status"}:
        invalid("Unknown fields")
    if creating and "title" not in data:
        invalid("Title is required")
    if not creating and not data:
        invalid("At least one field is required")
    result = {}
    for name, maximum in (("title", 200), ("description", 2000)):
        if name in data:
            value = data[name]
            if not isinstance(value, str) or len(value) > maximum:
                invalid(f"{name} must be a string of at most {maximum} characters")
            if name == "title" and not value.strip():
                invalid("Title must not be blank")
            result[name] = value.strip() if name == "title" else value
    if "status" in data:
        if not isinstance(data["status"], str) or data["status"] not in (
            "TODO",
            "IN_PROGRESS",
            "DONE",
        ):
            invalid("Invalid task status")
        result["status"] = data["status"]
    return result


def city(value):
    if not isinstance(value, str) or not 2 <= len(value.strip()) <= 80:
        invalid("City must contain 2 to 80 characters")
    value = value.strip()
    if not all(c.isalpha() or c in " -'.," for c in value):
        invalid("City contains invalid characters")
    return value
