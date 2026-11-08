from datetime import UTC, datetime
from uuid import uuid4

from src.models.validation import fields


def now():
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


class TaskService:
    def __init__(self, repository):
        self.repository = repository

    def create(self, data):
        data = fields(data, creating=True)
        timestamp = now()
        return self.repository.create(
            {
                "task_id": str(uuid4()),
                "description": "",
                "status": "TODO",
                **data,
                "created_at": timestamp,
                "updated_at": timestamp,
            }
        )

    def update(self, task_id, data):
        changes = fields(data)
        return self.repository.update(task_id, {**changes, "updated_at": now()})
