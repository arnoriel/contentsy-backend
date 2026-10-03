import os
import re
import uuid
from pathlib import Path, PureWindowsPath

from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

from app.core.config import get_settings
from app.models.upload import Upload

CHUNK_SIZE = 1024 * 1024
SNIFF_BYTES = 16

# ext -> (container family, mime). Magic bytes jadi sumber kebenaran, bukan filename/Content-Type dari client.
ALLOWED_FORMATS: dict[str, tuple[str, str]] = {
    ".mp4": ("isobmff", "video/mp4"),
    ".m4v": ("isobmff", "video/x-m4v"),
    ".mov": ("isobmff", "video/quicktime"),
    ".mkv": ("matroska", "video/x-matroska"),
    ".webm": ("matroska", "video/webm"),
    ".avi": ("avi", "video/x-msvideo"),
}


class UploadRejected(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def sniff_container(head: bytes) -> str | None:
    if head[4:8] == b"ftyp":
        return "isobmff"
    if head[:4] == b"\x1a\x45\xdf\xa3":
        return "matroska"
    if head[:4] == b"RIFF" and head[8:12] == b"AVI ":
        return "avi"
    return None


def sanitize_filename(name: str | None) -> str:
    base = PureWindowsPath(name or "").name  # handle separator / dan \
    base = re.sub(r"[\x00-\x1f\x7f]", "", base).strip()
    return base[:255] or "video"


def resolve_path(upload: Upload) -> Path:
    return get_settings().upload_path / upload.stored_name


def _copy_limited(src, dest: Path, max_bytes: int) -> int:
    total = 0
    with open(dest, "wb") as out:
        while chunk := src.read(CHUNK_SIZE):
            total += len(chunk)
            if total > max_bytes:
                raise UploadRejected(413, f"File too large. Max {get_settings().max_upload_size_mb} MB")
            out.write(chunk)
    return total


def store_video(db: Session, user_id: uuid.UUID, file: UploadFile) -> Upload:
    settings = get_settings()
    original = sanitize_filename(file.filename)
    ext = Path(original).suffix.lower()
    if ext not in ALLOWED_FORMATS:
        allowed = ", ".join(sorted(ALLOWED_FORMATS))
        raise UploadRejected(415, f"Unsupported video format. Allowed: {allowed}")
    container, mime = ALLOWED_FORMATS[ext]

    head = file.file.read(SNIFF_BYTES)
    if not head:
        raise UploadRejected(422, "File is empty")
    if sniff_container(head) != container:
        raise UploadRejected(415, "File content does not match its video format")
    file.file.seek(0)

    upload_id = uuid.uuid4()
    stored_name = f"{upload_id}{ext}"
    dest = settings.upload_path / stored_name
    tmp = settings.upload_path / f"{upload_id}.part"
    settings.upload_path.mkdir(parents=True, exist_ok=True)

    try:
        size = _copy_limited(file.file, tmp, settings.max_upload_bytes)
        os.replace(tmp, dest)  # atomic: file final tidak pernah setengah-tertulis
        record = Upload(
            id=upload_id,
            user_id=user_id,
            original_filename=original,
            stored_name=stored_name,
            content_type=mime,
            size_bytes=size,
        )
        db.add(record)
        db.commit()
    except BaseException:
        db.rollback()
        tmp.unlink(missing_ok=True)
        dest.unlink(missing_ok=True)
        raise
    return record
