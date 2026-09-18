"""Skill and Project data models."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Skill:
    """Represents a skill with an optional completion status."""

    name: str
    completed: bool = False

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("Skill name cannot be empty.")

    def to_dict(self) -> dict:
        return {"name": self.name, "completed": self.completed}

    @classmethod
    def from_dict(cls, data: dict) -> "Skill":
        return cls(name=data["name"], completed=data.get("completed", False))


@dataclass
class Project:
    """Represents a completed project."""

    title: str
    description: Optional[str] = ""

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        if not self.title:
            raise ValueError("Project title cannot be empty.")

    def to_dict(self) -> dict:
        return {"title": self.title, "description": self.description}

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        return cls(title=data["title"], description=data.get("description", ""))
