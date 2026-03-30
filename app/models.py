from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import Column, DateTime, JSON
from sqlmodel import Field, SQLModel



def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OnsenStay(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    agent_label: str | None = None
    visit_reason: str
    mood: str
    current_activity: str
    onsen_slug: str
    variant_slug: str
    state: str = Field(default='active')
    turn_count: int = Field(default=0)
    meta_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column('meta_json', JSON))
    created_at: datetime = Field(default_factory=utcnow, sa_column=Column('created_at', DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=utcnow, sa_column=Column('updated_at', DateTime(timezone=True), nullable=False))
    expires_at: datetime | None = Field(default=None, sa_column=Column('expires_at', DateTime(timezone=True), nullable=True))


class StayTurn(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    stay_id: str = Field(index=True)
    role: str
    activity: str
    content_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column('content_json', JSON))
    created_at: datetime = Field(default_factory=utcnow, sa_column=Column('created_at', DateTime(timezone=True), nullable=False))
