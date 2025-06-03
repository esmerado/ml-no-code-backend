# schemas.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str


class User(BaseModel):
    id: UUID
    email: str

    class Config:
        orm_mode = True


class JobCreate(BaseModel):
    user_id: UUID
    job_name: str
    model_name: str
    metric_name: str
    metric_value: str


class Job(BaseModel):
    id: UUID
    job_name: str
    model_name: str
    metric_name: str
    metric_value: str
    created_at: datetime

    class Config:
        orm_mode = True
