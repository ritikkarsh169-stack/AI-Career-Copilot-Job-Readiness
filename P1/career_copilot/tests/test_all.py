"""
Pytest unit tests for AI Career Copilot
========================================
Covers:
  - Profile validation
  - Skill / Project models
  - Skill-gap analysis
  - Job-readiness calculation
  - Learning progress (roadmap)
  - Interview prep
  - Data persistence
  - Invalid inputs and edge cases
"""

import json
import os
import tempfile

import pytest

from career_copilot.models.profile import VALID_JOB_ROLES, UserProfile
from career_copilot.models.skill import Project, Skill
from career_copilot.services.analyzer import CareerAnalyzer, SkillGapReport
from career_copilot.services.interview import InterviewPrep
from career_copilot.services.readiness import JobReadinessCalculator, WEIGHTS
from career_copilot.services.storage import DataStorage


# ===========================================================================
# Helpers / Fixtures
# ===========================================================================

def make_profile(
    name: str = "Alice",
    education: str = "BSc Computer Science",
    target_role: str = "Python Developer",
    current_skills=None,
    projects=None,
    skills_to_learn=None,
    interview_practice=None,
) -> UserProfile:
    return UserProfile(
        name=name,
        education=education,
        target_role=target_role,
        current_skills=current_skills or [],
        projects=projects or [],
        skills_to_learn=skills_to_learn or [],
        interview_practice=interview_practice or [],
    )


@pytest.fixture
def analyzer() -> CareerAnalyzer:
    return CareerAnalyzer()


@pytest.fixture
def calculator(analyzer: CareerAnalyzer) -> JobReadinessCalculator:
    return JobReadinessCalculator(analyzer)


@pytest.fixture
def interview() -> InterviewPrep:
    return InterviewPrep()


@pytest.fixture
def tmp_storage(tmp_path) -> DataStorage:
    """DataStorage backed by a temp directory — isolated per test."""
    filepath = str(tmp_path / "test_profile.json")
    return DataStorage(filepath=filepath)


# ===========================================================================
# 1. Skill model
# ===========================================================================

class TestSkillModel:
    def test_skill_creation(self):
        s = Skill(name="Python")
        assert s.name == "Python"
        assert s.completed is False

    def test_skill_completed_flag(self):
        s = Skill(name="Git", completed=True)
        assert s.completed is True

    def test_skill_strips_whitespace(self):
        s = Skill(name="  Docker  ")
        assert s.name == "Docker"

    def test_skill_empty_name_raises(self):
        with pytest.raises(ValueError):
            Skill(name="")

    def test_skill_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            Skill(name="   ")

    def test_skill_to_dict(self):
        s = Skill(name="Python", completed=True)
        d = s.to_dict()
        assert d == {"name": "Python", "completed": True}

    def test_skill_from_dict(self):
        s = Skill.from_dict({"name": "SQL", "completed": False})
        assert s.name == "SQL"
        assert s.completed is False

    def test_skill_from_dict_default_completed(self):
        s = Skill.from_dict({"name": "SQL"})
        assert s.completed is False


# ===========================================================================
# 2. Project model
# ===========================================================================

class TestProjectModel:
    def test_project_creation(self):
        p = Project(title="Portfolio Website")
        assert p.title == "Portfolio Website"
        assert p.description == ""

    def test_project_strips_whitespace(self):
        p = Project(title="  My App  ")
        assert p.title == "My App"

    def test_project_empty_title_raises(self):
        with pytest.raises(ValueError):
            Project(title="")

    def test_project_to_dict(self):
        p = Project(title="API Project", description="A REST API")
        d = p.to_dict()
        assert d == {"title": "API Project", "description": "A REST API"}

    def test_project_from_dict(self):
        p = Project.from_dict({"title": "CLI App", "description": ""})
        assert p.title == "CLI App"


# ===========================================================================
# 3. UserProfile validation
# ===========================================================================

class TestUserProfile:
    def test_valid_profile(self):
        p = make_profile()
        assert p.name == "Alice"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="Name cannot be empty"):
            make_profile(name="")

    def test_whitespace_name_raises(self):
        with pytest.raises(ValueError, match="Name cannot be empty"):
            make_profile(name="   ")

    def test_invalid_role_raises(self):
        with pytest.raises(ValueError, match="Invalid target role"):
            make_profile(target_role="Astronaut")

    def test_valid_roles_accepted(self):
        for role in VALID_JOB_ROLES:
            p = make_profile(target_role=role)
            assert p.target_role == role

    def test_to_dict_round_trip(self):
        skills = [Skill("Python"), Skill("Git")]
        projects = [Project("App", "A cool app")]
        p = make_profile(current_skills=skills, projects=projects)
        d = p.to_dict()
        p2 = UserProfile.from_dict(d)
        assert p2.name == p.name
        assert p2.target_role == p.target_role
        assert len(p2.current_skills) == 2
        assert len(p2.projects) == 1

    def test_from_dict_missing_optional_fields(self):
        data = {"name": "Bob", "target_role": "Web Developer", "education": ""}
        p = UserProfile.from_dict(data)
        assert p.current_skills == []
        assert p.projects == []


# ===========================================================================
# 4. CareerAnalyzer — skill-gap analysis
# ===========================================================================

class TestCareerAnalyzer:
    def test_returns_skill_gap_report(self, analyzer):
        profile = make_profile(current_skills=[Skill("Python"), Skill("Git")])
        report = analyzer.analyze(profile)
        assert isinstance(report, SkillGapReport)

    def test_present_skills_identified(self, analyzer):
        profile = make_profile(current_skills=[Skill("Python"), Skill("Git")])
        report = analyzer.analyze(profile)
        assert "Python" in report.present_skills
        assert "Git" in report.present_skills

    def test_missing_skills_identified(self, analyzer):
        profile = make_profile(current_skills=[Skill("Python")])
        report = analyzer.analyze(profile)
        # The role requires more than just Python
        assert len(report.missing_skills) > 0

    def test_zero_skills_zero_match(self, analyzer):
        profile = make_profile(current_skills=[])
        report = analyzer.analyze(profile)
        assert report.match_percentage == 0.0
        assert report.present_skills == []

    def test_all_skills_full_match(self, analyzer):
        required = analyzer.get_required_skills("Python Developer")
        skills = [Skill(name=s) for s in required]
        profile = make_profile(current_skills=skills)
        report = analyzer.analyze(profile)
        assert report.match_percentage == 100.0
        assert report.missing_skills == []

    def test_case_insensitive_matching(self, analyzer):
        profile = make_profile(current_skills=[Skill("python"), Skill("git")])
        report = analyzer.analyze(profile)
        assert "Python" in report.present_skills
        assert "Git" in report.present_skills

    def test_summary_string(self, analyzer):
        profile = make_profile(current_skills=[Skill("Python")])
        report = analyzer.analyze(profile)
        assert "Python Developer" in report.summary()

    def test_get_required_skills_unknown_role(self, analyzer):
        skills = analyzer.get_required_skills("Unknown Role")
        assert skills == []


# ===========================================================================
# 5. Learning roadmap
# ===========================================================================

class TestLearningRoadmap:
    def test_roadmap_returns_steps(self, analyzer):
        profile = make_profile()
        steps = analyzer.build_roadmap(profile)
        assert len(steps) > 0

    def test_roadmap_steps_are_initially_incomplete(self, analyzer):
        profile = make_profile()
        steps = analyzer.build_roadmap(profile)
        assert all(not step.completed for step in steps)

    def test_roadmap_step_completion_persists(self, analyzer):
        profile = make_profile()
        steps = analyzer.build_roadmap(profile)
        # Mark the first step complete by storing it in skills_to_learn
        profile.skills_to_learn = [
            Skill(name=steps[0].description, completed=True)
        ]
        new_steps = analyzer.build_roadmap(profile)
        assert new_steps[0].completed is True

    def test_roadmap_step_to_dict(self, analyzer):
        profile = make_profile()
        steps = analyzer.build_roadmap(profile)
        d = steps[0].to_dict()
        assert "index" in d
        assert "description" in d
        assert "completed" in d

    def test_roadmap_step_indices_sequential(self, analyzer):
        profile = make_profile()
        steps = analyzer.build_roadmap(profile)
        for i, step in enumerate(steps):
            assert step.index == i


# ===========================================================================
# 6. JobReadinessCalculator
# ===========================================================================

class TestJobReadinessCalculator:
    def test_score_zero_for_empty_profile(self, calculator):
        profile = make_profile()
        result = calculator.calculate(profile)
        # Skills = 0, Projects = 0, Education = full (provided), interview = 0, progress = 0
        assert result.total_score > 0   # education gives points
        assert result.total_score <= 100

    def test_score_100_for_complete_profile(self, calculator, analyzer):
        required = analyzer.get_required_skills("Python Developer")
        skills = [Skill(name=s) for s in required]
        roadmap_steps = analyzer.build_roadmap(
            make_profile(target_role="Python Developer")
        )
        skills_to_learn = [
            Skill(name=step.description, completed=True) for step in roadmap_steps
        ]
        questions = InterviewPrep().get_questions("Python Developer")
        profile = make_profile(
            current_skills=skills,
            projects=[Project(f"Project {i}") for i in range(3)],
            skills_to_learn=skills_to_learn,
            interview_practice=questions[:3],
        )
        result = calculator.calculate(profile)
        assert result.total_score == 100.0

    def test_score_is_between_0_and_100(self, calculator):
        profile = make_profile(current_skills=[Skill("Python")])
        result = calculator.calculate(profile)
        assert 0 <= result.total_score <= 100

    def test_weights_sum_to_100(self):
        assert sum(WEIGHTS.values()) == 100

    def test_result_has_five_factors(self, calculator):
        profile = make_profile()
        result = calculator.calculate(profile)
        assert len(result.factors) == 5

    def test_grade_A_for_high_score(self, calculator, analyzer):
        required = analyzer.get_required_skills("Python Developer")
        skills = [Skill(name=s) for s in required]
        questions = InterviewPrep().get_questions("Python Developer")
        profile = make_profile(
            current_skills=skills,
            projects=[Project(f"P{i}") for i in range(3)],
            interview_practice=questions[:3],
        )
        result = calculator.calculate(profile)
        assert result.grade in ("A", "B")

    def test_grade_F_for_empty_profile_no_education(self, calculator):
        # Education is empty → only 0 pts possible
        profile = make_profile(education="")
        # Manually override to no education
        profile.education = ""
        result = calculator.calculate(profile)
        assert result.grade == "F"

    def test_factor_names_are_present(self, calculator):
        profile = make_profile()
        result = calculator.calculate(profile)
        names = {f.name for f in result.factors}
        assert "Required Skills" in names
        assert "Projects" in names
        assert "Education" in names
        assert "Interview Preparation" in names
        assert "Learning Progress" in names

    def test_education_factor_earns_full_when_provided(self, calculator):
        profile = make_profile(education="BSc CS")
        result = calculator.calculate(profile)
        edu_factor = next(f for f in result.factors if f.name == "Education")
        assert edu_factor.earned == WEIGHTS["education"]

    def test_education_factor_zero_when_missing(self, calculator):
        profile = make_profile(education="")
        profile.education = ""
        result = calculator.calculate(profile)
        edu_factor = next(f for f in result.factors if f.name == "Education")
        assert edu_factor.earned == 0.0


# ===========================================================================
# 7. Interview Prep
# ===========================================================================

class TestInterviewPrep:
    def test_get_questions_returns_list(self, interview):
        questions = interview.get_questions("Python Developer")
        assert isinstance(questions, list)
        assert len(questions) > 0

    def test_unknown_role_returns_empty(self, interview):
        questions = interview.get_questions("Astronaut")
        assert questions == []

    def test_mark_practiced_adds_question(self, interview):
        profile = make_profile()
        q = interview.get_questions("Python Developer")[0]
        interview.mark_practiced(profile, q)
        assert q in profile.interview_practice

    def test_mark_practiced_no_duplicates(self, interview):
        profile = make_profile()
        q = interview.get_questions("Python Developer")[0]
        interview.mark_practiced(profile, q)
        interview.mark_practiced(profile, q)
        assert profile.interview_practice.count(q) == 1

    def test_mark_practiced_empty_raises(self, interview):
        profile = make_profile()
        with pytest.raises(ValueError):
            interview.mark_practiced(profile, "")

    def test_get_pending_excludes_practiced(self, interview):
        profile = make_profile()
        q = interview.get_questions("Python Developer")[0]
        interview.mark_practiced(profile, q)
        pending = interview.get_pending_questions(profile)
        assert q not in pending

    def test_get_practiced_includes_marked(self, interview):
        profile = make_profile()
        q = interview.get_questions("Python Developer")[0]
        interview.mark_practiced(profile, q)
        practiced = interview.get_practiced_questions(profile)
        assert q in practiced

    def test_all_roles_have_questions(self, interview):
        for role in VALID_JOB_ROLES:
            questions = interview.get_questions(role)
            assert len(questions) > 0, f"No questions for role: {role}"


# ===========================================================================
# 8. Data persistence
# ===========================================================================

class TestDataStorage:
    def test_save_and_load(self, tmp_storage):
        profile = make_profile(
            current_skills=[Skill("Python")],
            projects=[Project("App")],
        )
        tmp_storage.save(profile)
        loaded = tmp_storage.load()
        assert loaded is not None
        assert loaded.name == "Alice"
        assert len(loaded.current_skills) == 1
        assert loaded.current_skills[0].name == "Python"

    def test_load_returns_none_when_no_file(self, tmp_storage):
        result = tmp_storage.load()
        assert result is None

    def test_save_creates_file(self, tmp_storage):
        profile = make_profile()
        tmp_storage.save(profile)
        assert os.path.exists(tmp_storage.filepath)

    def test_delete_removes_file(self, tmp_storage):
        profile = make_profile()
        tmp_storage.save(profile)
        tmp_storage.delete()
        assert not os.path.exists(tmp_storage.filepath)

    def test_load_corrupted_file_raises_value_error(self, tmp_storage):
        with open(tmp_storage.filepath, "w") as f:
            f.write("THIS IS NOT JSON {{{")
        with pytest.raises(ValueError, match="corrupted"):
            tmp_storage.load()

    def test_load_invalid_data_raises_value_error(self, tmp_storage):
        bad_data = {"name": "", "target_role": "Python Developer"}
        with open(tmp_storage.filepath, "w") as f:
            json.dump(bad_data, f)
        with pytest.raises(ValueError):
            tmp_storage.load()

    def test_round_trip_preserves_interview_practice(self, tmp_storage):
        profile = make_profile(interview_practice=["What is Python?"])
        tmp_storage.save(profile)
        loaded = tmp_storage.load()
        assert loaded.interview_practice == ["What is Python?"]

    def test_round_trip_preserves_skills_to_learn(self, tmp_storage):
        profile = make_profile(
            skills_to_learn=[Skill("Learn Python basics", completed=True)]
        )
        tmp_storage.save(profile)
        loaded = tmp_storage.load()
        assert loaded.skills_to_learn[0].completed is True

    def test_overwrite_existing_file(self, tmp_storage):
        profile1 = make_profile(name="Alice")
        tmp_storage.save(profile1)
        profile2 = make_profile(name="Bob", target_role="Web Developer")
        tmp_storage.save(profile2)
        loaded = tmp_storage.load()
        assert loaded.name == "Bob"


# ===========================================================================
# 9. Edge cases
# ===========================================================================

class TestEdgeCases:
    def test_profile_with_many_skills(self, analyzer):
        skills = [Skill(f"Skill{i}") for i in range(50)]
        profile = make_profile(current_skills=skills)
        report = analyzer.analyze(profile)
        assert report.match_percentage >= 0

    def test_profile_with_no_projects_zero_project_score(self, calculator):
        profile = make_profile(projects=[])
        result = calculator.calculate(profile)
        project_factor = next(f for f in result.factors if f.name == "Projects")
        assert project_factor.earned == 0.0

    def test_profile_with_max_projects_full_project_score(self, calculator):
        projects = [Project(f"P{i}") for i in range(10)]
        profile = make_profile(projects=projects)
        result = calculator.calculate(profile)
        project_factor = next(f for f in result.factors if f.name == "Projects")
        assert project_factor.earned == WEIGHTS["projects"]

    def test_skill_gap_summary_contains_role(self, analyzer):
        profile = make_profile(target_role="Data Scientist")
        report = analyzer.analyze(profile)
        assert "Data Scientist" in report.summary()

    def test_calculator_verdict_is_string(self, calculator):
        profile = make_profile()
        result = calculator.calculate(profile)
        assert isinstance(result.verdict, str)
        assert len(result.verdict) > 0

    def test_roadmap_for_all_roles(self, analyzer):
        for role in VALID_JOB_ROLES:
            profile = make_profile(target_role=role)
            steps = analyzer.build_roadmap(profile)
            assert len(steps) > 0, f"No roadmap steps for role: {role}"

    def test_profile_from_dict_with_all_fields(self):
        data = {
            "name": "Carol",
            "education": "MSc AI",
            "target_role": "Data Scientist",
            "current_skills": [{"name": "Python", "completed": False}],
            "skills_to_learn": [{"name": "Learn stats", "completed": True}],
            "projects": [{"title": "ML Project", "description": ""}],
            "interview_practice": ["What is overfitting?"],
        }
        p = UserProfile.from_dict(data)
        assert p.name == "Carol"
        assert p.skills_to_learn[0].completed is True
        assert p.interview_practice[0] == "What is overfitting?"
