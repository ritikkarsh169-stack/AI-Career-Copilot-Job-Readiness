"""
AI Career Copilot — Streamlit UI
=================================
Pages:
  1. 👤 My Profile
  2. 📊 Career Analysis
  3. 🏆 Job Readiness Score
  4. 🎤 Interview Prep
"""

import streamlit as st

from career_copilot.models.profile import VALID_JOB_ROLES, UserProfile
from career_copilot.models.skill import Project, Skill
from career_copilot.services.analyzer import CareerAnalyzer
from career_copilot.services.interview import InterviewPrep
from career_copilot.services.readiness import JobReadinessCalculator
from career_copilot.services.storage import DataStorage

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Career Copilot",
    page_icon="🚀",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Service singletons (cached so they are created only once)
# ---------------------------------------------------------------------------

@st.cache_resource
def get_services():
    analyzer = CareerAnalyzer()
    calculator = JobReadinessCalculator(analyzer)
    interview = InterviewPrep()
    storage = DataStorage()
    return analyzer, calculator, interview, storage


analyzer, calculator, interview_prep, storage = get_services()

# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------

def _init_session() -> None:
    """Load profile from disk once per session."""
    if "profile" not in st.session_state:
        try:
            saved = storage.load()
        except ValueError as e:
            st.warning(f"⚠️ Could not load saved profile: {e}")
            saved = None
        st.session_state["profile"] = saved
    if "success_msg" not in st.session_state:
        st.session_state["success_msg"] = ""


def _save_profile() -> None:
    profile: UserProfile = st.session_state["profile"]
    storage.save(profile)
    st.session_state["success_msg"] = "✅ Profile saved."


def _get_profile() -> UserProfile | None:
    return st.session_state.get("profile")


# ---------------------------------------------------------------------------
# Page: My Profile
# ---------------------------------------------------------------------------

def page_profile() -> None:
    st.header("👤 My Profile")
    st.write("Fill in your details and save. All fields marked \\* are required.")

    profile: UserProfile | None = _get_profile()

    # Pre-populate from existing profile or blank defaults
    default_name      = profile.name           if profile else ""
    default_education = profile.education      if profile else ""
    default_role_idx  = (VALID_JOB_ROLES.index(profile.target_role)
                         if profile else 0)
    default_skills    = ", ".join(s.name for s in profile.current_skills)  if profile else ""
    default_projects  = "\n".join(p.title for p in profile.projects)       if profile else ""

    with st.form("profile_form"):
        name       = st.text_input("Full Name *", value=default_name)
        education  = st.text_area("Education Details", value=default_education,
                                  placeholder="e.g. BSc Computer Science, 2023")
        target_role = st.selectbox("Target Job Role *", VALID_JOB_ROLES,
                                   index=default_role_idx)
        skills_raw = st.text_input(
            "Current Skills (comma-separated) *",
            value=default_skills,
            placeholder="e.g. Python, Git, SQL",
        )
        projects_raw = st.text_area(
            "Completed Projects (one per line)",
            value=default_projects,
            placeholder="e.g. Portfolio website\nTo-do app in Python",
        )
        submitted = st.form_submit_button("💾 Save Profile")

    if submitted:
        errors = []

        # Validate name
        if not name.strip():
            errors.append("Name is required.")

        # Validate skills
        skill_names = [s.strip() for s in skills_raw.split(",") if s.strip()]
        if not skill_names:
            errors.append("Please enter at least one current skill.")

        # Validate projects
        project_titles = [p.strip() for p in projects_raw.splitlines() if p.strip()]

        if errors:
            for err in errors:
                st.error(err)
        else:
            try:
                new_skills = [Skill(name=n) for n in skill_names]
                new_projects = [Project(title=t) for t in project_titles]

                # Preserve roadmap completion state from old profile
                old_skills_to_learn = profile.skills_to_learn if profile else []
                # Preserve interview practice
                old_interview = profile.interview_practice if profile else []

                new_profile = UserProfile(
                    name=name.strip(),
                    education=education.strip(),
                    target_role=target_role,
                    current_skills=new_skills,
                    skills_to_learn=old_skills_to_learn,
                    projects=new_projects,
                    interview_practice=old_interview,
                )
                st.session_state["profile"] = new_profile
                _save_profile()
                st.success("✅ Profile saved successfully!")
            except ValueError as e:
                st.error(f"Validation error: {e}")

    # Show current profile summary
    if profile:
        with st.expander("📋 Current Profile Summary", expanded=False):
            st.write(f"**Name:** {profile.name}")
            st.write(f"**Education:** {profile.education or '—'}")
            st.write(f"**Target Role:** {profile.target_role}")
            st.write(f"**Skills:** {', '.join(s.name for s in profile.current_skills) or '—'}")
            st.write(f"**Projects:** {len(profile.projects)}")


# ---------------------------------------------------------------------------
# Page: Career Analysis
# ---------------------------------------------------------------------------

def page_career_analysis() -> None:
    st.header("📊 Career Analysis")

    profile = _get_profile()
    if not profile:
        st.info("👈 Please complete your profile first.")
        return

    # --- Skill-Gap Report ---
    st.subheader("🔍 Skill-Gap Report")
    report = analyzer.analyze(profile)
    st.write(report.summary())

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**✅ Skills You Have**")
        if report.present_skills:
            for skill in report.present_skills:
                st.write(f"• {skill}")
        else:
            st.write("None matched yet.")
    with col2:
        st.markdown("**❌ Skills You're Missing**")
        if report.missing_skills:
            for skill in report.missing_skills:
                st.write(f"• {skill}")
        else:
            st.success("You have all required skills! 🎉")

    st.progress(int(report.match_percentage))

    # --- Learning Roadmap ---
    st.subheader("🗺️ Learning Roadmap")
    st.write(
        f"Follow these steps to become a **{profile.target_role}**. "
        "Check off a step when you complete it."
    )

    roadmap = analyzer.build_roadmap(profile)
    if not roadmap:
        st.info("No roadmap available for this role.")
        return

    # Sync completion state: render checkboxes and persist changes
    updated = False
    for step in roadmap:
        checked = st.checkbox(
            f"Step {step.index + 1}: {step.description}",
            value=step.completed,
            key=f"roadmap_{step.index}",
        )
        if checked != step.completed:
            updated = True
            step.completed = checked

    if updated:
        # Persist the updated roadmap state into profile.skills_to_learn
        profile.skills_to_learn = [
            Skill(name=step.description, completed=step.completed)
            for step in roadmap
        ]
        _save_profile()
        st.toast("Progress saved!")


# ---------------------------------------------------------------------------
# Page: Job Readiness Score
# ---------------------------------------------------------------------------

def page_readiness() -> None:
    st.header("🏆 Job Readiness Score")

    profile = _get_profile()
    if not profile:
        st.info("👈 Please complete your profile first.")
        return

    result = calculator.calculate(profile)

    # Big score display
    score_color = (
        "#2ecc71" if result.total_score >= 70
        else "#f39c12" if result.total_score >= 40
        else "#e74c3c"
    )
    st.markdown(
        f"<h1 style='text-align:center; color:{score_color};'>"
        f"{result.total_score:.0f} / 100</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<h3 style='text-align:center;'>Grade: {result.grade}</h3>",
        unsafe_allow_html=True,
    )
    st.info(result.verdict)

    st.progress(int(result.total_score))

    # Factor breakdown
    st.subheader("📐 How Your Score Was Calculated")
    st.write(
        "Your score is built from five clearly defined factors. "
        "Every point is explained below."
    )

    for factor in result.factors:
        pct = factor.earned / factor.weight * 100 if factor.weight else 0
        with st.expander(
            f"**{factor.name}** — {factor.earned:.0f} / {factor.weight} pts "
            f"({pct:.0f}%)"
        ):
            st.write(factor.explanation)
            st.progress(int(pct))

    # Tips
    st.subheader("💡 Tips to Improve Your Score")
    for factor in result.factors:
        if factor.earned < factor.weight:
            gap = factor.weight - factor.earned
            st.write(f"• **{factor.name}**: You can still earn {gap:.0f} more point(s).")


# ---------------------------------------------------------------------------
# Page: Interview Prep
# ---------------------------------------------------------------------------

def page_interview() -> None:
    st.header("🎤 Interview Preparation")

    profile = _get_profile()
    if not profile:
        st.info("👈 Please complete your profile first.")
        return

    all_questions = interview_prep.get_questions(profile.target_role)
    pending       = interview_prep.get_pending_questions(profile)
    practiced     = interview_prep.get_practiced_questions(profile)

    st.write(
        f"Practice interview questions for **{profile.target_role}**. "
        f"You have practised **{len(practiced)} / {len(all_questions)}** questions."
    )
    st.progress(
        int(len(practiced) / len(all_questions) * 100) if all_questions else 0
    )

    # --- Questions to practice ---
    st.subheader("📝 Questions to Practice")
    if not pending:
        st.success("🎉 You've practised all questions for this role!")
    else:
        for i, question in enumerate(pending):
            with st.expander(f"Q{i + 1}: {question}"):
                answer = st.text_area(
                    "Write your answer here (optional — just for practice):",
                    key=f"answer_{i}",
                    height=100,
                )
                if st.button("✅ Mark as Practised", key=f"mark_{i}"):
                    interview_prep.mark_practiced(profile, question)
                    _save_profile()
                    st.rerun()

    # --- Already practiced ---
    if practiced:
        st.subheader("✅ Already Practised")
        for q in practiced:
            st.write(f"• {q}")


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main() -> None:
    _init_session()

    st.title("🚀 AI Career Copilot")
    st.caption("Your personal job-readiness assistant — track skills, analyse gaps, and prepare for interviews.")

    if st.session_state.get("success_msg"):
        st.toast(st.session_state["success_msg"])
        st.session_state["success_msg"] = ""

    page = st.sidebar.radio(
        "Navigate",
        ["👤 My Profile", "📊 Career Analysis", "🏆 Job Readiness Score", "🎤 Interview Prep"],
    )

    if page == "👤 My Profile":
        page_profile()
    elif page == "📊 Career Analysis":
        page_career_analysis()
    elif page == "🏆 Job Readiness Score":
        page_readiness()
    elif page == "🎤 Interview Prep":
        page_interview()

    st.sidebar.markdown("---")
    st.sidebar.caption("AI Career Copilot v1.0")


if __name__ == "__main__":
    main()
