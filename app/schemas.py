from typing import Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    candidate_name: str = Field(min_length=1, max_length=128)
    university_id: str
    position: str = Field(min_length=1, max_length=256)
    offer_date: str
    deadline: str
    idempotency_key: Optional[str] = None


class TaskEventIn(BaseModel):
    external_event_id: str = Field(min_length=4, max_length=128)
    event_type: str
    expected_version: int


class ResolveAnomalyIn(BaseModel):
    actor: str = "HR"


class AcceptAnomalyIn(BaseModel):
    actor: str = "HR"


class PublishRuleIn(BaseModel):
    actor: str = "HR规则管理员"
    change_note: str = "完成公开来源核验与双人复核"
