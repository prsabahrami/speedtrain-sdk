import base64
import json
from typing import Any

from .client import call_rpc, get_context
from .types import Message, Task, TaskSplit


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
    payload: dict = {}
    notebook_type = ctx.get("notebookType")
    if notebook_type == "NOTEBOOK_TYPE_REWARD":
        preprocessed_dataset_id = ctx.get("preprocessedDatasetId")
        if not preprocessed_dataset_id:
            raise RuntimeError("Notebook not attached to any preprocessed dataset")
        payload["trainingDatasetId"] = preprocessed_dataset_id
    else:
        payload["rawDatasetId"] = ctx["rawDatasetId"]

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


def set_task_split(*, task_id: str, split: TaskSplit) -> Task:
    if not isinstance(split, TaskSplit):
        raise TypeError("split must be a TaskSplit")
    response = call_rpc("SetTaskSplit", {"id": task_id, "split": split.value})
    return Task.from_api_response(response)


def set_ground_truth(*, task_id: str, ground_truth: bytes | None) -> Task:
    if ground_truth is None:
        response = call_rpc("ClearTaskGroundTruth", {"id": task_id})
        return Task.from_api_response(response)
    response = call_rpc(
        "SetTaskGroundTruth",
        {
            "id": task_id,
            "groundTruth": base64.b64encode(ground_truth).decode("ascii"),
        },
    )
    return Task.from_api_response(response)


def serialize_content_part(part: dict[str, Any]) -> dict[str, Any]:
    data: dict[str, Any] = {"type": part.get("type", "")}
    if "text" in part:
        data["text"] = part["text"]
    image_url = part.get("imageUrl") or part.get("image_url")
    if image_url:
        if isinstance(image_url, dict):
            data["imageUrl"] = {"url": image_url.get("url", "")}
        else:
            data["imageUrl"] = {"url": str(image_url)}
    return data


def serialize_message(message: Message) -> dict[str, Any]:
    data: dict[str, Any] = {"role": message.role}
    if message.content_text is not None:
        data["contentText"] = message.content_text
    if message.content_parts:
        data["contentParts"] = [
            serialize_content_part(part) for part in message.content_parts
        ]
    return data


def normalize_status(status: str) -> str:
    if not status:
        return "TASK_STATUS_UNSPECIFIED"
    status_upper = status.upper()
    if status_upper.startswith("TASK_STATUS_"):
        return status_upper
    mapped = STATUS_MAP.get(status.lower())
    if not mapped:
        raise ValueError(f"Invalid status: {status}")
    return mapped


def serialize_task(task: Task) -> dict[str, Any]:
    data: dict[str, Any] = {
        "documentPath": task.document_path,
        "trace": [serialize_message(msg) for msg in task.trace],
        "metadataJson": json.dumps(task.metadata),
        "sourceFileId": task.source_file_id,
        "status": normalize_status(task.status),
    }
    if task.completion is not None:
        data["completion"] = {"text": task.completion.text}
    if task.ground_truth is not None:
        data["groundTruth"] = base64.b64encode(task.ground_truth).decode("ascii")
    if task.reward is not None:
        data["reward"] = task.reward
    if task.error:
        data["error"] = task.error
    return data


def save_preprocessed_tasks(tasks: list[Task]) -> dict[str, Any]:
    ctx = get_context()
    payload = {
        "rawDatasetId": ctx["rawDatasetId"],
        "tasks": [serialize_task(task) for task in tasks],
    }
    response = call_rpc("SavePreprocessedTasks", payload)
    return {
        "preprocessed_dataset_id": response.get("preprocessedDatasetId", ""),
        "task_ids": response.get("taskIds", []),
    }


def update_status(task_id: str, status: str) -> Task:
    status_value = STATUS_MAP.get(status.lower())
    if not status_value:
        raise ValueError(f"Invalid status: {status}")

    response = call_rpc(
        "UpdateTaskStatus",
        {"id": task_id, "status": status_value},
    )
    return Task.from_api_response(response)
