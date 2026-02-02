import uuid
from pathlib import Path


DOCUMENTS_ROOT = "/data/documents"
OUTPUTS_ROOT = "/data/outputs"


def save_file(data: bytes, filename: str, subdir: str | None = None) -> str:
    file_id = str(uuid.uuid4())

    if subdir:
        output_dir = Path(OUTPUTS_ROOT) / subdir
    else:
        output_dir = Path(OUTPUTS_ROOT)

    output_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(filename).suffix
    output_path = output_dir / f"{file_id}{ext}"

    with open(output_path, "wb") as f:
        f.write(data)

    return str(output_path)


def load_document(document_path: str) -> bytes:
    full_path = document_path
    if not document_path.startswith("/"):
        full_path = f"{DOCUMENTS_ROOT}/{document_path}"

    with open(full_path, "rb") as f:
        return f.read()
