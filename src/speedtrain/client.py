import os
from pathlib import Path
import httpx

API_URL = os.environ.get(
    "SPEEDTRAIN_API_URL",
    "https://speedtrain--speedtrain-speedtrain-api.modal.run"
)

_client: httpx.Client | None = None
_context: dict | None = None


def get_http_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(base_url=API_URL, timeout=30.0)
    return _client


def call_rpc(method: str, payload: dict) -> dict:
    client = get_http_client()
    response = client.post(
        f"/speedtrain.Speedtrain/{method}",
        json=payload,
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    return response.json()


def get_context() -> dict:
    global _context
    if _context is None:
        notebook_path = os.environ.get("JPY_SESSION_NAME")
        if not notebook_path:
            raise RuntimeError("Must run from Speedtrain notebook")
        notebook_id = Path(notebook_path).stem
        _context = call_rpc("GetNotebookContext", {"notebookId": notebook_id})
        if not _context.get("rawDatasetId"):
            raise RuntimeError("Notebook not attached to any dataset")
    return _context


def get_raw_dataset_id() -> str:
    return get_context()["rawDatasetId"]


def get_notebook_type() -> str:
    ntype = get_context().get("notebookType", "")
    return ntype.replace("NOTEBOOK_TYPE_", "").lower()
