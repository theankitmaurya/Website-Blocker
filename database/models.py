"""Data models for Website Blocker."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Website:
    id: Optional[int]
    domain: str
    category_id: Optional[int] = None
    enabled: bool = True
    created_at: str = ""
    updated_at: str = ""
    name: Optional[str] = None

    @property
    def display_name(self) -> str:
        if self.name:
            return self.name
        from utils.validators import get_website_name
        return get_website_name(self.domain)


@dataclass
class Session:
    id: Optional[int]
    start_time: str
    end_time: Optional[str]
    duration_seconds: int
    type: str = "manual"  # "manual" | "scheduled" | "focus"
    status: str = "active"  # "active" | "completed" | "interrupted" | "stopped"
    created_at: str = ""


@dataclass
class Schedule:
    id: Optional[int]
    name: str
    start_time: str
    end_time: str
    days: str  # JSON list string e.g. '["Mon", "Tue"]'
    enabled: bool = True
    created_at: str = ""


@dataclass
class Setting:
    key: str
    value: str
