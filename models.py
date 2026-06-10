import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict


class AdCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    owner: str = Field(..., min_length=1)


class Ad(AdCreate):
    id: str
    created_at: datetime

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


ads_db: dict[str, Ad] = {}
