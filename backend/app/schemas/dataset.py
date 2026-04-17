from pydantic import BaseModel


class DatasetConnectRequest(BaseModel):
    connection_string: str | None = None
    endpoint: str | None = None
    api_key: str | None = None


class DatasetPreviewResponse(BaseModel):
    dataset_id: str
    columns: list[str]
    rows: list[dict]
