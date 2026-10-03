from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile  # bukan fastapi.UploadFile: request.form() mengembalikan class Starlette
from starlette.formparsers import MultiPartException

from app.api.deps import require_credit
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.upload import UploadOut
from app.services import upload_service

router = APIRouter(tags=["upload"])

MULTIPART_OVERHEAD_BYTES = 1024 * 1024  # boundary + header part

# Endpoint tidak pakai File(...) supaya auth & credit check jalan SEBELUM body diparse/di-spool ke disk.
_OPENAPI_BODY = {
    "requestBody": {
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "required": ["file"],
                    "properties": {"file": {"type": "string", "format": "binary"}},
                }
            }
        },
    }
}


def _check_content_length(request: Request) -> None:
    raw = request.headers.get("content-length")
    if raw is None or not raw.isdigit():
        raise HTTPException(status.HTTP_411_LENGTH_REQUIRED, "Content-Length header required")
    settings = get_settings()
    if int(raw) > settings.max_upload_bytes + MULTIPART_OVERHEAD_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"File too large. Max {settings.max_upload_size_mb} MB"
        )


@router.post(
    "/upload",
    response_model=UploadOut,
    status_code=status.HTTP_201_CREATED,
    openapi_extra=_OPENAPI_BODY,
)
async def upload_video(
    request: Request,
    user: User = Depends(require_credit),
    db: Session = Depends(get_db),
):
    _check_content_length(request)
    try:
        form = await request.form(max_files=1, max_fields=10)
    except MultiPartException as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, exc.message) from None

    try:
        file = form.get("file")
        if not isinstance(file, UploadFile):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Field 'file' (multipart/form-data) is required")
        try:
            return await run_in_threadpool(upload_service.store_video, db, user.id, file)
        except upload_service.UploadRejected as exc:
            raise HTTPException(exc.status_code, exc.detail) from None
    finally:
        await form.close()
