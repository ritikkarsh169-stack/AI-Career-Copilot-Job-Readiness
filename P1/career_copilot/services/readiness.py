"""JobReadinessCalculator — transparent, explainable scoring."""

from dataclasses import dataclass
from typing import Dict, List

from career_copilot.models.profile import UserProfile
from career_copilot.services.analyzer import CareerAnalyzer, SkillGapReport

# ---------------------------------------------------------------------------
# Score weights (must sum to 100)
# ---------------------------------------------------------------------------
WEIGHTS: Dict[str, int] = {
    "skills":            40,   # How many required skills the user has
    "projects":          20,   # Number of completed projects
    "education":         15,   # Has education details filled in
    "interview_prep":    15,   # Has practised interview questions
    "learning_progress": 10,   # Roadmap steps marked as complete
}

assert sum(WEIGHTS.values()) == 100, "Score weights must sum to 100."


@dataclass
class ScoreFactor:
    """A single factor contributing to the readiness score."""

    name: str
    weight: int          # max points available
    earned: float        # points actually earned
    explanation: str     # human-readable reason


@dataclass
class ReadinessResult:
    """Complete job-readiness assessment result."""

    total_score: float              # 0–100
    factors: List[ScoreFactor]
    grade: str                      # A / B / C / D / F
    verdict: str                    # short motivating message

    def breakdown_text(self) -> str:
        lines = [f"**Total score: {self.total_score:.0f} / 100 — {self.grade}**\n"]
        for f in self.factors:
            lines.append(
                f"- **{f.name}** ({f.earned:.0f}/{f.weight} pts): {f.explanation}"
            )
        return "\n".join(lines)


class JobReadinessCalculator:
    """
    Calculates an explainable job-readiness score based on five clearly
    defined factors.  No opaque AI scores — every point is traceable.
    """

    # Thresholds for project scoring
    MAX_PROJECTS_FOR_FULL_SCORE: int = 3
    # Thresholds for interview practice
    MIN_PRACTICED_QUESTIONS: int = 3

    def __init__(self, analyzer: CareerAnalyzer) -> None:
        self._analyzer = analyzer

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate(self, profile: UserProfile) -> ReadinessResult:
        """Run all five scoring factors and return a ReadinessResult."""
        gap_report: SkillGapReport = self._analyzer.analyze(profile)
        roadmap = self._analyzer.build_roadmap(profile)

        factors: List[ScoreFactor] = [
            self._score_skills(gap_report),
            self._score_projects(profile),
            self._score_education(profile),
            self._score_interview_prep(profile),
            self._score_learning_progress(roadmap),
        ]

        total = sum(f.earned for f in factors)
        total = round(min(total, 100.0), 1)

        grade = self._grade(total)
        verdict = self._verdict(total)

        return ReadinessResult(
            total_score=total,
            factors=factors,
            grade=grade,
            verdict=verdict,
        )

    # ------------------------------------------------------------------
    # Private factor scorers
    # ------------------------------------------------------------------

    def _score_skills(self, gap: SkillGapReport) -> ScoreFactor:
        weight = WEIGHTS["skills"]
        earned = round(gap.match_percentage / 100 * weight, 1)
        explanation = (
            f"You have {len(gap.present_skills)} of {len(gap.required_skills)} "
            f"required skills ({gap.match_percentage:.0f}% coverage)."
        )
        return ScoreFactor("Required Skills", weight, earned, explanation)

    def _score_projects(self, profile: UserProfile) -> ScoreFactor:
        weight = WEIGHTS["projects"]
        count = len(profile.projects)
        max_c = self.MAX_PROJECTS_FOR_FULL_SCORE
        ratio = min(count / max_c, 1.0) if max_c > 0 else 0.0
        earned = round(ratio * weight, 1)
        explanation = (
            f"You have {count} project(s). "
            f"{max_c}+ projects earns full marks."
        )
        return ScoreFactor("Projects", weight, earned, explanation)

    def _score_education(self, profile: UserProfile) -> ScoreFactor:
        weight = WEIGHTS["education"]
        has_education = bool(profile.education and profile.education.strip())
        earned = float(weight) if has_education else 0.0
        explanation = (
            "Education details provided."
            if has_education
            else "No education details entered — add them to earn these points."
        )
        return ScoreFactor("Education", weight, earned, explanation)

    def _score_interview_prep(self, profile: UserProfile) -> ScoreFactor:
        weight = WEIGHTS["interview_prep"]
        practiced = len(profile.interview_practice)
        min_q = self.MIN_PRACTICED_QUESTIONS
        ratio = min(practiced / min_q, 1.0) if min_q > 0 else 0.0
        earned = round(ratio * weight, 1)
        explanation = (
            f"You have practised {practiced} interview question(s). "
            f"Practise at least {min_q} to earn full marks."
        )
        return ScoreFactor("Interview Preparation", weight, earned, explanation)

    def _score_learning_progress(self, roadmap) -> ScoreFactor:
        weight = WEIGHTS["learning_progress"]
        total_steps = len(roadmap)
        if total_steps == 0:
            earned = 0.0
            explanation = "No roadmap steps available for this role."
        else:
            completed = sum(1 for step in roadmap if step.completed)
            ratio = completed / total_steps
            earned = round(ratio * weight, 1)
            explanation = (
                f"You have completed {completed} of {total_steps} roadmap step(s) "
                f"({ratio * 100:.0f}%)."
            )
        return ScoreFactor("Learning Progress", weight, earned, explanation)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 85:
            return "A"
        if score >= 70:
            return "B"
        if score >= 55:
            return "C"
        if score >= 40:
            return "D"
        return "F"

    @staticmethod
    def _verdict(score: float) -> str:
        if score >= 85:
            return "🎉 Excellent! You are well-prepared — start applying now."
        if score >= 70:
            return "👍 Good progress! Strengthen a few areas before applying."
        if score >= 55:
            return "📚 You're on the right track. Keep building your skills."
        if score >= 40:
            return "🔨 More work needed. Focus on the missing skills and projects."
        return "🚀 You're just getting started — follow the roadmap step by step."
