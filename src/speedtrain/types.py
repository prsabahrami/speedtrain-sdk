from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str
    content_text: str | None = None
    content_parts: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Completion:
    text: str
    model: str | None = None
    tokens: int | None = None


@dataclass
class Task:
    id: str
    document_path: str
    trace: list[Message]
    metadata: dict[str, Any]
    source_file_id: str
    status: str
    reward: float | None = None
    completion: Completion | None = None
    error: str | None = None

    @classmethod
    def from_api_response(cls, data: dict) -> "Task":
        trace = [
            Message(
                role=msg.get("role", ""),
                content_text=msg.get("contentText"),
                content_parts=msg.get("contentParts", []),
            )
            for msg in data.get("trace", [])
        ]

        completion = None
        comp_data = data.get("completion")
        if comp_data:
            completion = Completion(
                text=comp_data.get("text", ""),
                model=comp_data.get("loraId") or comp_data.get("baseModelId"),
                tokens=None,
            )

        import json
        metadata_json = data.get("metadataJson", "{}")
        metadata = json.loads(metadata_json) if metadata_json else {}

        status_raw = data.get("status", "TASK_STATUS_UNSPECIFIED")
        status = status_raw.replace("TASK_STATUS_", "").lower()

        return cls(
            id=data.get("id", ""),
            document_path=data.get("documentPath", ""),
            trace=trace,
            metadata=metadata,
            source_file_id=data.get("sourceFileId", ""),
            status=status,
            reward=data.get("reward"),
            completion=completion,
            error=data.get("error"),
        )
