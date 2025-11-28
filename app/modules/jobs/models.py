from sqlalchemy import Column, String, Text, DateTime, UniqueConstraint
from app.utils.models import BaseModel
from datetime import datetime


class TaskRun(BaseModel):
    """Model to track job execution with idempotency support"""
    __tablename__ = "task_runs"
    __table_args__ = (
        UniqueConstraint("name", "idempotency_key", name="uq_taskrun_name_key"),
    )

    name = Column(String(128), nullable=False, index=True)
    idempotency_key = Column(String(255), nullable=False, index=True)
    status = Column(
        String(32), nullable=False, default="processing"
    )  # processing|success|failed
    last_error = Column(Text, nullable=True)
    
    # Note: created_at and updated_at are inherited from BaseModel
    
    def __repr__(self):
        return f"<TaskRun(name='{self.name}', idempotency_key='{self.idempotency_key}', status='{self.status}')>"
