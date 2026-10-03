import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UploadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    upload_id: uuid.UUID = Field(validation_alias="id")
    filename: str = Field(validation_alias="original_filename")
    size_bytes: int
    content_type: str
    created_at: datetime
