from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="starter")
    settings_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    users: Mapped[list["User"]] = relationship(back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="Viewer")
    org_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organization: Mapped[Organization | None] = relationship(back_populates="users")
    datasets: Mapped[list["Dataset"]] = relationship(back_populates="user")


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(512))
    schema_json: Mapped[dict] = mapped_column(JSON, default=dict)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="datasets")
    audits: Mapped[list["Audit"]] = relationship(back_populates="dataset")


class Audit(Base):
    __tablename__ = "audits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"))
    model_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    dataset: Mapped[Dataset] = relationship(back_populates="audits")
    results: Mapped[list["AuditResult"]] = relationship(back_populates="audit")


class AuditResult(Base):
    __tablename__ = "audit_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    audit_id: Mapped[str] = mapped_column(ForeignKey("audits.id"), index=True)
    metric_name: Mapped[str] = mapped_column(String(128))
    group_name: Mapped[str] = mapped_column(String(128))
    value: Mapped[float] = mapped_column(Float)
    threshold: Mapped[float] = mapped_column(Float)
    passed: Mapped[bool] = mapped_column(Boolean)

    audit: Mapped[Audit] = relationship(back_populates="results")


class Remediation(Base):
    __tablename__ = "remediations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    audit_id: Mapped[str] = mapped_column(ForeignKey("audits.id"))
    strategy: Mapped[str] = mapped_column(String(128))
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    before_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    after_metrics: Mapped[dict] = mapped_column(JSON, default=dict)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    audit_id: Mapped[str] = mapped_column(ForeignKey("audits.id"), unique=True)
    pdf_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Monitor(Base):
    __tablename__ = "monitors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    audit_id: Mapped[str] = mapped_column(ForeignKey("audits.id"))
    schedule_cron: Mapped[str] = mapped_column(String(64))
    alert_config: Mapped[dict] = mapped_column(JSON, default=dict)
    last_run: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    monitor_id: Mapped[str] = mapped_column(ForeignKey("monitors.id"))
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metric: Mapped[str] = mapped_column(String(128))
    value: Mapped[float] = mapped_column(Float)
    notified: Mapped[bool] = mapped_column(Boolean, default=False)
