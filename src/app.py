import hmac
import json
import logging
import os
import time
from functools import lru_cache

from botocore.exceptions import BotoCoreError, ClientError

from src.handlers.router import route
from src.repositories.dynamodb import build_repository
from src.services.weather import WeatherService
from src.utils.errors import ApiError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@lru_cache(maxsize=1)
def repository():
    return build_repository()


weather = WeatherService()


def make_handler(repository_factory=repository, weather_service=weather):
    def handler(event, context):
        start = time.monotonic()
        request_id = getattr(context, "aws_request_id", "local")
        headers = {str(k).lower(): v for k, v in (event.get("headers") or {}).items()}
        response_headers = {
            "content-type": "application/json; charset=utf-8",
            "cache-control": "no-store",
            "x-content-type-options": "nosniff",
        }
        origin = os.environ.get("ALLOWED_ORIGIN", "http://localhost:8080")
        if headers.get("origin") == origin:
            response_headers.update({"access-control-allow-origin": origin, "vary": "Origin"})
        method = event.get("requestContext", {}).get("http", {}).get("method", "")
        path = event.get("rawPath", "")
        try:
            if method == "OPTIONS":
                if headers.get("origin") != origin:
                    raise ApiError(403, "ORIGIN_DENIED", "Origin not allowed")
                response_headers.update(
                    {
                        "access-control-allow-methods": "GET,POST,PATCH,DELETE,OPTIONS",
                        "access-control-allow-headers": "content-type,authorization",
                    }
                )
                status, payload = 204, None
            else:
                if path != "/health":
                    token = os.environ.get("DEMO_TOKEN", "")
                    if len(token) < 32:
                        raise ApiError(503, "NOT_CONFIGURED", "Demo access is not configured")
                    supplied = str(headers.get("authorization", ""))
                    if not hmac.compare_digest(supplied.encode(), f"Bearer {token}".encode()):
                        raise ApiError(401, "UNAUTHORIZED", "Valid demo token required")
                status, payload = route(event, repository_factory, weather_service)
        except ApiError as exc:
            status = exc.status
            payload = {
                "error": {"code": exc.code, "message": exc.message},
                "request_id": request_id,
            }
        except (BotoCoreError, ClientError):
            status = 503
            payload = {
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "Database temporarily unavailable",
                },
                "request_id": request_id,
            }
        except Exception:
            # Do not log exception messages, payloads, headers or credentials.
            status = 500
            payload = {
                "error": {"code": "INTERNAL_ERROR", "message": "Internal server error"},
                "request_id": request_id,
            }
        logger.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "status": status,
                    "duration_ms": round((time.monotonic() - start) * 1000, 2),
                }
            )
        )
        return {
            "statusCode": status,
            "headers": response_headers,
            "body": "" if status == 204 else json.dumps(payload, ensure_ascii=False),
        }

    return handler


lambda_handler = make_handler()
