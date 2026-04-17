from pydantic import BaseModel, Field


class MonitorCreate(BaseModel):
    audit_id: str
    schedule_cron: str
    alert_config: dict = Field(default_factory=dict)
