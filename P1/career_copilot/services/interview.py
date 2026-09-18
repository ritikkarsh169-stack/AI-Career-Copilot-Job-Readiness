"""InterviewPrep — provides role-specific beginner interview questions."""

import json
import os
from typing import Dict, List

from career_copilot.models.profile import UserProfile

_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "job_roles.json")


def _load_role_data() -> Dict:
    path = os.path.normpath(_DATA_FILE)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class InterviewPrep:
    """
    Provides interview questions for a user's target role.
    Tracks which questions the user has already practised.
    """

    def __init__(self) -> None:
        self._role_data: Dict = _load_role_data()

    def get_questions(self, role: str) -> List[str]:
        """Return the interview questions for a given role."""
        return self._role_data.get(role, {}).get("interview_questions", [])

    def mark_practiced(self, profile: UserProfile, question: str) -> None:
        """
        Record that the user has practised a specific question.
        Prevents duplicates.
        """
        question = question.strip()
        if not question:
            raise ValueError("Question text cannot be empty.")
        if question not in profile.interview_practice:
            profile.interview_practice.append(question)

    def get_pending_questions(self, profile: UserProfile) -> List[str]:
        """Return questions the user hasn't practised yet."""
        all_questions = self.get_questions(profile.target_role)
        return [q for q in all_questions if q not in profile.interview_practice]

    def get_practiced_questions(self, profile: UserProfile) -> List[str]:
        """Return questions the user has already practised."""
        all_questions = self.get_questions(profile.target_role)
        return [q for q in all_questions if q in profile.interview_practice]
