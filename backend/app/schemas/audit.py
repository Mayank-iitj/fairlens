from datetime import datetime

from pydantic import BaseModel


class AuditCreate(BaseModel):
    dataset_id: str
    model_path: str | None = None
    config_json: dict = {}


class AuditOut(BaseModel):
    id: str
    dataset_id: str
    status: str
    score: float | None
    created_at: datetime

    class Config:
        from_attributes = True
