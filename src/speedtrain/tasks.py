from .client import call_rpc, get_context
from .types import Task


STATUS_MAP = {
    "pending": "TASK_STATUS_PENDING",
    "downloaded": "TASK_STATUS_DOWNLOADED",
    "inferencing": "TASK_STATUS_INFERENCING",
    "inferred": "TASK_STATUS_INFERRED",
    "rewarding": "TASK_STATUS_REWARDING",
    "ready": "TASK_STATUS_READY",
    "failed": "TASK_STATUS_FAILED",
}


def get_tasks(status: str | None = None) -> list[Task]:
    ctx = get_context()
    payload: dict = {"rawDatasetId": ctx["rawDatasetId"]}

    if status:
        status_upper = status.upper()
        if status_upper in STATUS_MAP.values():
            payload["status"] = status_upper
        elif status.lower() in STATUS_MAP:
            payload["status"] = STATUS_MAP[status.lower()]

    response = call_rpc("ListTasks", payload)
    tasks_data = response.get("tasks", [])
    return [Task.from_api_response(t) for t in tasks_data]


def get_task(task_id: str) -> Task:
    response = call_rpc("GetTask", {"id": task_id})
    return Task.from_api_response(response)


def set_reward(task_id: str, reward: float) -> Task:
    if not 0.0 <= reward <= 1.0:
        raise ValueError(f"Reward must be between 0 and 1, got {reward}")

    response = call_rpc("SetTaskReward", {"id": task_id, "reward": reward})
    return Task.from_api_response(response)


def set_error(task_id: str, error: str) -> Task:
    response = call_rpc("SetTaskError", {"id": task_id, "error": error})
    return Task.from_api_response(response)


def mark_processed(task_ids: list[str]) -> int:
    response = call_rpc(
        "BatchUpdateTaskStatus",
        {"ids": task_ids, "status": "TASK_STATUS_INFERRED"},
    )
    return response.get("updatedCount", 0)


def update_status(task_id: str, status: str) -> Task:
    status_value = STATUS_MAP.get(status.lower())
    if not status_value:
        raise ValueError(f"Invalid status: {status}")

    response = call_rpc(
        "UpdateTaskStatus",
        {"id": task_id, "status": status_value},
    )
    return Task.from_api_response(response)
