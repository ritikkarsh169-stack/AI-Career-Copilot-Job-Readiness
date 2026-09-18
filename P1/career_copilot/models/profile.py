"""UserProfile model."""

from dataclasses import dataclass, field
from typing import List

from career_copilot.models.skill import Project, Skill

VALID_JOB_ROLES: List[str] = [
    "Python Developer",
    "Data Scientist",
    "Web Developer",
    "Machine Learning Engineer",
    "DevOps Engineer",
    "Mobile App Developer",
    "Cybersecurity Analyst",
    "Cloud Engineer",
]


@dataclass
class UserProfile:
    """Stores all information about a user."""

    name: str
    education: str
    target_role: str
    current_skills: List[Skill] = field(default_factory=list)
    skills_to_learn: List[Skill] = field(default_factory=list)
    projects: List[Project] = field(default_factory=list)
    interview_practice: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("Name cannot be empty.")
        if self.target_role not in VALID_JOB_ROLES:
            raise ValueError(
                f"Invalid target role '{self.target_role}'. "
                f"Must be one of: {', '.join(VALID_JOB_ROLES)}"
            )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "education": self.education,
            "target_role": self.target_role,
            "current_skills": [s.to_dict() for s in self.current_skills],
            "skills_to_learn": [s.to_dict() for s in self.skills_to_learn],
            "projects": [p.to_dict() for p in self.projects],
            "interview_practice": self.interview_practice,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        return cls(
            name=data["name"],
            education=data.get("education", ""),
            target_role=data["target_role"],
            current_skills=[Skill.from_dict(s) for s in data.get("current_skills", [])],
            skills_to_learn=[Skill.from_dict(s) for s in data.get("skills_to_learn", [])],
            projects=[Project.from_dict(p) for p in data.get("projects", [])],
            interview_practice=data.get("interview_practice", []),
        )
