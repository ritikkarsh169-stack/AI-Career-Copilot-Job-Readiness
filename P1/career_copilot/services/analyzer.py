"""CareerAnalyzer — skill-gap analysis and learning roadmap."""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List

from career_copilot.models.profile import UserProfile
from career_copilot.models.skill import Skill

_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "job_roles.json")


def _load_role_data() -> Dict:
    """Load the static job-role data from JSON."""
    path = os.path.normpath(_DATA_FILE)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@dataclass
class SkillGapReport:
    """Result of a skill-gap analysis."""

    target_role: str
    required_skills: List[str]
    present_skills: List[str]      # user has these
    missing_skills: List[str]      # user does NOT have these
    match_percentage: float        # 0–100

    def summary(self) -> str:
        return (
            f"You have {len(self.present_skills)} of {len(self.required_skills)} "
            f"required skills for {self.target_role} "
            f"({self.match_percentage:.0f}% match)."
        )


@dataclass
class RoadmapStep:
    """A single step in a learning roadmap."""

    index: int
    description: str
    completed: bool = False

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "description": self.description,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RoadmapStep":
        return cls(
            index=data["index"],
            description=data["description"],
            completed=data.get("completed", False),
        )


class CareerAnalyzer:
    """
    Analyses a user's skills against their target role and
    produces a skill-gap report plus a step-by-step roadmap.
    """

    def __init__(self) -> None:
        self._role_data: Dict = _load_role_data()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_required_skills(self, role: str) -> List[str]:
        """Return the list of required skills for a role."""
        return self._role_data.get(role, {}).get("required_skills", [])

    def analyze(self, profile: UserProfile) -> SkillGapReport:
        """Compare the user's skills to the target role requirements."""
        required = self.get_required_skills(profile.target_role)
        user_skill_names = {s.name.lower() for s in profile.current_skills}

        present: List[str] = []
        missing: List[str] = []

        for skill in required:
            if skill.lower() in user_skill_names:
                present.append(skill)
            else:
                missing.append(skill)

        match_pct = (len(present) / len(required) * 100) if required else 0.0

        return SkillGapReport(
            target_role=profile.target_role,
            required_skills=required,
            present_skills=present,
            missing_skills=missing,
            match_percentage=round(match_pct, 1),
        )

    def build_roadmap(self, profile: UserProfile) -> List[RoadmapStep]:
        """
        Return the ordered roadmap steps for the target role.
        Merges persisted completion state from the profile's skills_to_learn list.
        """
        raw_steps: List[str] = self._role_data.get(
            profile.target_role, {}
        ).get("roadmap", [])

        # Build a lookup of persisted completion state by step text
        completed_lookup: Dict[str, bool] = {
            s.name.lower(): s.completed for s in profile.skills_to_learn
        }

        steps: List[RoadmapStep] = []
        for i, description in enumerate(raw_steps):
            completed = completed_lookup.get(description.lower(), False)
            steps.append(RoadmapStep(index=i, description=description, completed=completed))

        return steps
