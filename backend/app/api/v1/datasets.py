import csv
import io
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Dataset, User
from app.db.session import get_db
from app.schemas.dataset import DatasetConnectRequest, DatasetPreviewResponse


router = APIRouter()


@router.get("")
def list_datasets(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    datasets = list(
        db.scalars(
            select(Dataset)
            .where(Dataset.user_id == user.id)
            .order_by(Dataset.created_at.desc())
        ).all()
    )
    return [
        {
            "id": item.id,
            "name": item.name,
            "row_count": item.row_count,
            "created_at": item.created_at,
        }
        for item in datasets
    ]


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form("uploaded-dataset"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    destination = Path("tmp") / file.filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    destination.write_bytes(content)
    row_count = 0
    schema_json: dict = {}
    if file.filename.endswith(".csv"):
        reader = csv.reader(io.StringIO(content.decode("utf-8", errors="ignore")))
        rows = list(reader)
        row_count = max(len(rows) - 1, 0)
        schema_json = {"columns": rows[0] if rows else []}
    dataset = Dataset(user_id=user.id, name=name, file_path=str(destination), row_count=row_count, schema_json=schema_json)
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return {"dataset_id": dataset.id, "row_count": dataset.row_count}


@router.post("/connect")
def connect_dataset(payload: DatasetConnectRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    source = payload.connection_string or payload.endpoint
    if not source:
        raise HTTPException(status_code=400, detail="Provide connection string or endpoint")
    dataset = Dataset(user_id=user.id, name="connected-source", file_path=source, row_count=0)
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return {"dataset_id": dataset.id, "source": source}


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def preview_dataset(dataset_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DatasetPreviewResponse:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    path = Path(dataset.file_path)
    if not path.exists() or not path.name.endswith(".csv"):
        return DatasetPreviewResponse(dataset_id=dataset_id, columns=["source"], rows=[{"source": dataset.file_path}])

    rows: list[dict] = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(row)
            if len(rows) >= 100:
                break
    columns = list(rows[0].keys()) if rows else []
    return DatasetPreviewResponse(dataset_id=dataset_id, columns=columns, rows=rows)
