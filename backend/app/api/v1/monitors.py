from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Monitor, User
from app.db.session import get_db
from app.schemas.monitor import MonitorCreate


router = APIRouter()


@router.get("")
def list_monitors(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    monitors = list(db.scalars(select(Monitor)).all())
    return [
        {
            "id": m.id,
            "audit_id": m.audit_id,
            "schedule_cron": m.schedule_cron,
            "alert_config": m.alert_config,
            "last_run": m.last_run,
            "next_run": m.next_run,
        }
        for m in monitors
    ]


@router.post("")
def create_monitor(payload: MonitorCreate, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    monitor = Monitor(
        audit_id=payload.audit_id,
        schedule_cron=payload.schedule_cron,
        alert_config=payload.alert_config,
        next_run=datetime.utcnow(),
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return {"monitor_id": monitor.id}


@router.delete("/{monitor_id}")
def delete_monitor(monitor_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    monitor = db.get(Monitor, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    db.delete(monitor)
    db.commit()
    return {"deleted": True}
