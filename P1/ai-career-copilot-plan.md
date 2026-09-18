# AI Career Copilot & Job Readiness — Implementation Plan

## Top-Level Overview

**Goal:** Build a beginner-friendly, single-session AI Career Copilot web app in Python using Streamlit.
The app walks a user through creating their career profile (skills, education, projects), selecting or defining a target job role,
analysing skill gaps, generating a personalised learning roadmap, calculating a job-readiness score,
and preparing for interviews — all persisted between runs via JSON and CSV files.

**Scope:**
- Single profile per session (no login, no multi-user)
- Hardcoded base roles + custom role option
- Skill-gap analysis driven by comparing user skills vs role-required skills
- Job-readiness score from 4 weighted factors (skills matched, education level, project count, roadmap progress)
- Interview questions generated dynamically from the user's specific skill gaps
- JSON for profile/progress; CSV for skill-gap results and scores
- OOP business logic layer, fully separated from Streamlit UI
- pytest unit tests for all business logic

**Non-goals:**
- Authentication / multi-user
- AI/LLM API calls
- Database (SQLite, Postgres, etc.)
- Deployment / CI-CD

---

## Sub-Task 1 — Project Scaffold and Folder Structure

**Intent:** Establish the folder/file skeleton so all subsequent sub-tasks have a home.
Every Python import path, data file path, and test file path is decided here.

**Expected Outcomes:**
- All folders and empty stub files exist
- `requirements.txt` lists every dependency
- `README.md` describes how to run the app and tests
- Project runs `streamlit run app.py` without crashing (empty shell)

**Folder & File Structure:**
```
ai_career_copilot/
├── app.py                        # Streamlit entry point (UI only)
├── requirements.txt
├── README.md
├── data/
│   ├── profiles/
│   │   └── profile.json          # Persisted user profile
│   ├── progress/
│   │   └── progress.json         # Persisted roadmap progress
│   └── results/
│       └── skill_gap_results.csv # Persisted skill-gap + score snapshots
├── core/
│   ├── __init__.py
│   ├── models.py                 # Dataclasses / data models
│   ├── profile_manager.py        # UserProfile CRUD + persistence
│   ├── role_manager.py           # Job roles, required skills, custom role
│   ├── skill_gap_analyzer.py     # Skill-gap analysis logic
│   ├── roadmap_generator.py      # Learning roadmap generation
│   ├── score_calculator.py       # Job-readiness score (4 weighted factors)
│   ├── interview_prep.py         # Dynamic interview question generation
│   └── progress_tracker.py      # Progress tracking logic
├── storage/
│   ├── __init__.py
│   ├── json_storage.py           # Load/save JSON files
│   └── csv_storage.py            # Append/read CSV files
├── ui/
│   ├── __init__.py
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── page_profile.py
│   │   ├── page_role_selection.py
│   │   ├── page_skill_gap.py
│   │   ├── page_roadmap.py
│   │   ├── page_score.py
│   │   ├── page_interview_prep.py
│   │   └── page_progress.py
│   └── components.py             # Shared Streamlit widgets / helpers
└── tests/
    ├── __init__.py
    ├── test_profile_manager.py
    ├── test_role_manager.py
    ├── test_skill_gap_analyzer.py
    ├── test_score_calculator.py
    ├── test_roadmap_generator.py
    ├── test_interview_prep.py
    └── test_progress_tracker.py
```

**Todo List:**
- [ ] Create all folders listed above
- [ ] Create all empty stub `.py` files with a module docstring only
- [ ] Write `requirements.txt` (streamlit, pytest)
- [ ] Write `README.md` with run instructions

**Relevant Context:** No existing codebase. Greenfield.

**Status:** [ ] pending

---

## Sub-Task 2 — Data Models (`core/models.py`)

**Intent:** Define all data shapes as Python dataclasses with type hints.
Every other module imports these models — getting them right first prevents cascading refactors.

**Expected Outcomes:**
- All dataclasses defined, importable, and serialisable to/from plain dicts
- No logic in models — pure data containers

**Models and Fields:**

### `UserProfile`
| Field | Type | Purpose |
|---|---|---|
| `name` | `str` | Display name |
| `target_role` | `str` | Selected or custom role title |
| `skills` | `list[str]` | Skills the user already has |
| `education_level` | `str` | One of: "high_school", "associate", "bachelor", "master", "phd", "bootcamp", "self_taught" |
| `projects` | `list[Project]` | User's listed projects |
| `created_at` | `str` | ISO timestamp |
| `updated_at` | `str` | ISO timestamp |

### `Project`
| Field | Type | Purpose |
|---|---|---|
| `title` | `str` | Project name |
| `description` | `str` | Short description |
| `skills_used` | `list[str]` | Technologies / skills used in this project |

### `JobRole`
| Field | Type | Purpose |
|---|---|---|
| `title` | `str` | Role display name |
| `required_skills` | `list[str]` | Skills needed for this role |
| `is_custom` | `bool` | True when user-defined |

### `SkillGapResult`
| Field | Type | Purpose |
|---|---|---|
| `matched_skills` | `list[str]` | User skills that match role requirements |
| `missing_skills` | `list[str]` | Required skills the user lacks |
| `extra_skills` | `list[str]` | User skills beyond the role requirements |
| `match_percentage` | `float` | matched / required * 100 |

### `RoadmapItem`
| Field | Type | Purpose |
|---|---|---|
| `skill` | `str` | The skill to learn |
| `resources` | `list[str]` | Suggested learning resources (static strings) |
| `priority` | `int` | 1 = high, 2 = medium, 3 = low |

### `LearningRoadmap`
| Field | Type | Purpose |
|---|---|---|
| `target_role` | `str` | Role this roadmap is for |
| `items` | `list[RoadmapItem]` | Ordered list of skills to learn |

### `ReadinessScore`
| Field | Type | Purpose |
|---|---|---|
| `total_score` | `float` | 0–100 composite score |
| `skill_score` | `float` | Contribution from skill match |
| `education_score` | `float` | Contribution from education level |
| `project_score` | `float` | Contribution from project count |
| `progress_score` | `float` | Contribution from roadmap completion |
| `label` | `str` | "Beginner", "Developing", "Ready", "Strong" |

### `InterviewQuestion`
| Field | Type | Purpose |
|---|---|---|
| `skill` | `str` | The skill this question targets |
| `question` | `str` | The interview question text |
| `tip` | `str` | A short answering tip |

### `ProgressRecord`
| Field | Type | Purpose |
|---|---|---|
| `skill` | `str` | Skill being tracked |
| `status` | `str` | "not_started", "in_progress", "completed" |
| `last_updated` | `str` | ISO timestamp |

**Todo List:**
- [ ] Define all dataclasses with type hints in `core/models.py`
- [ ] Add a `to_dict()` and `from_dict()` classmethod to each model for JSON serialisation
- [ ] Write no logic — models are pure data containers

**Relevant Context:** `core/models.py` is imported by every other `core/` module.

**Status:** [ ] pending

---

## Sub-Task 3 — Storage Layer (`storage/`)

**Intent:** Isolate all file I/O behind two simple modules so business logic never touches file paths or format details.
This makes testing easy (business logic can be tested without real files) and swapping storage easy later.

**Expected Outcomes:**
- `json_storage.py` can load and save any dict/list to a `.json` file path
- `csv_storage.py` can append a row dict and read all rows from a `.csv` file path
- Both handle missing files gracefully (return empty data, not errors)

**Modules:**

### `storage/json_storage.py`
| Function | Signature | Responsibility |
|---|---|---|
| `load_json` | `(path: str) -> dict` | Read JSON file; return `{}` if missing |
| `save_json` | `(path: str, data: dict) -> None` | Write dict as JSON; create dirs if needed |

### `storage/csv_storage.py`
| Function | Signature | Responsibility |
|---|---|---|
| `append_csv_row` | `(path: str, row: dict, fieldnames: list[str]) -> None` | Append one row; write header if file is new |
| `read_csv_rows` | `(path: str) -> list[dict]` | Read all rows; return `[]` if file missing |

**Todo List:**
- [ ] Implement `load_json` and `save_json` in `storage/json_storage.py`
- [ ] Implement `append_csv_row` and `read_csv_rows` in `storage/csv_storage.py`
- [ ] Both modules must handle `FileNotFoundError` silently (return empty default)

**Relevant Context:** Used by `profile_manager.py`, `progress_tracker.py`, and `score_calculator.py`.

**Status:** [ ] pending

---

## Sub-Task 4 — Role Manager (`core/role_manager.py`)

**Intent:** Centralise all job-role knowledge.
Hardcoded base roles prevent users from having to define everything from scratch,
while the custom role option preserves full flexibility.

**Expected Outcomes:**
- A dictionary of 6–8 hardcoded roles with their required skill lists is available
- `get_all_roles()` returns all base role titles
- `get_role(title)` returns the `JobRole` dataclass for a given title
- `create_custom_role(title, skills)` returns a `JobRole` with `is_custom=True`

**Hardcoded Base Roles (initial set):**
1. Data Scientist — Python, SQL, Machine Learning, Statistics, Data Visualisation, Pandas, NumPy
2. Backend Developer — Python, REST APIs, SQL, Git, Docker, OOP, Testing
3. Frontend Developer — HTML, CSS, JavaScript, React, Git, Responsive Design
4. Full Stack Developer — HTML, CSS, JavaScript, Python, SQL, REST APIs, Git
5. DevOps Engineer — Linux, Docker, CI/CD, Git, Shell Scripting, Cloud Platforms
6. Machine Learning Engineer — Python, Machine Learning, Deep Learning, SQL, Git, MLOps
7. Data Analyst — SQL, Excel, Python, Data Visualisation, Statistics, Reporting

**Functions:**
| Function | Signature | Responsibility |
|---|---|---|
| `get_all_role_titles` | `() -> list[str]` | Return list of all base role title strings |
| `get_role` | `(title: str) -> JobRole or None` | Look up a base role by title |
| `create_custom_role` | `(title: str, skills: list[str]) -> JobRole` | Build a custom `JobRole` |

**Todo List:**
- [ ] Define the `ROLES` constant (dict of title -> required skills)
- [ ] Implement `get_all_role_titles`, `get_role`, `create_custom_role`

**Relevant Context:** Called from `page_role_selection.py` and `skill_gap_analyzer.py`.

**Status:** [ ] pending

---

## Sub-Task 5 — Profile Manager (`core/profile_manager.py`)

**Intent:** Manage the single user profile for the session — creation, updates, and persistence.
Keeping this in its own class means the UI never writes JSON directly.

**Expected Outcomes:**
- `ProfileManager` class can create, update, load, and save a `UserProfile`
- Profile is stored at `data/profiles/profile.json`
- All input is validated before the profile is saved (see validation rules below)

**Class: `ProfileManager`**
| Method | Responsibility |
|---|---|
| `__init__(self, storage_path: str)` | Set file path; load existing profile if present |
| `create_profile(name, target_role, skills, education_level, projects) -> UserProfile` | Build and save a new `UserProfile` |
| `update_skills(skills: list[str]) -> None` | Replace skills list and save |
| `update_education(level: str) -> None` | Replace education level and save |
| `add_project(project: Project) -> None` | Append project and save |
| `remove_project(title: str) -> None` | Remove project by title and save |
| `update_target_role(role: str) -> None` | Update target role and save |
| `get_profile() -> UserProfile or None` | Return current in-memory profile |
| `profile_exists() -> bool` | True if a profile is currently loaded |
| `_save() -> None` | Internal: persist in-memory profile to JSON |
| `_load() -> None` | Internal: read JSON into in-memory profile |

**Validation Rules (enforced in create/update methods):**
- `name`: non-empty string, max 100 chars
- `skills`: list of non-empty strings, no duplicates, max 50 items
- `education_level`: must be one of the 7 allowed values
- `target_role`: non-empty string
- `projects`: `title` required; `skills_used` must be a list

**Todo List:**
- [ ] Implement `ProfileManager` class with all methods above
- [ ] Add input validation helpers (raise `ValueError` with clear messages on bad input)
- [ ] Wire `_save` / `_load` to `storage/json_storage.py`

**Relevant Context:** `core/models.py` (UserProfile, Project), `storage/json_storage.py`.

**Status:** [ ] pending

---

## Sub-Task 6 — Skill Gap Analyzer (`core/skill_gap_analyzer.py`)

**Intent:** Pure comparison logic — no file I/O, no UI.
Takes user skills and a role's required skills and produces a `SkillGapResult`.
Keeping it pure makes it trivially testable.

**Expected Outcomes:**
- `SkillGapAnalyzer.analyze()` returns a correct `SkillGapResult`
- Comparison is case-insensitive and whitespace-normalised
- Result is also saved as a row in `data/results/skill_gap_results.csv`

**Class: `SkillGapAnalyzer`**
| Method | Responsibility |
|---|---|
| `__init__(self, csv_path: str)` | Store CSV path for result persistence |
| `analyze(user_skills: list[str], role: JobRole) -> SkillGapResult` | Compute matched, missing, extra skills and percentage |
| `save_result(result: SkillGapResult, role_title: str) -> None` | Append result snapshot to CSV |

**CSV Row Fields for `skill_gap_results.csv`:**
`timestamp, role_title, matched_skills, missing_skills, match_percentage`

**Skill Matching Rules:**
- Normalise both sides: lowercase + strip whitespace
- A skill counts as matched if the normalised string is in the normalised required set
- `match_percentage = len(matched) / len(required) * 100` (0.0 if required is empty)

**Todo List:**
- [ ] Implement `SkillGapAnalyzer` with `analyze()` and `save_result()` methods
- [ ] Normalise skill strings before comparison
- [ ] Wire CSV persistence to `storage/csv_storage.py`

**Relevant Context:** `core/models.py` (SkillGapResult, JobRole), `storage/csv_storage.py`.

**Status:** [ ] pending

---

## Sub-Task 7 — Roadmap Generator (`core/roadmap_generator.py`)

**Intent:** Turn a `SkillGapResult`'s `missing_skills` list into an ordered, prioritised `LearningRoadmap`.
Static resource suggestions are fine — no external API needed.

**Expected Outcomes:**
- `RoadmapGenerator.generate()` returns a `LearningRoadmap` with one `RoadmapItem` per missing skill
- Each item has at least one static resource string and a priority value

**Class: `RoadmapGenerator`**
| Method | Responsibility |
|---|---|
| `generate(gap: SkillGapResult, role: JobRole) -> LearningRoadmap` | Build ordered roadmap from missing skills |
| `_get_resources(skill: str) -> list[str]` | Return static resource suggestions for a skill |
| `_assign_priority(skill: str, role: JobRole) -> int` | Priority 1 if skill is in top-3 required; 2 otherwise |

**Static Resources Strategy:**
- A small internal dict maps known skill names to curated resource links/names (e.g., "Python" -> ["Python.org Official Docs", "Automate the Boring Stuff"])
- For unknown skills, return a generic suggestion: `["Search on YouTube", "Search on freeCodeCamp"]`

**Priority Logic:**
- Skills that appear first in the role's `required_skills` list get priority 1 (most important)
- All others get priority 2
- Roadmap items are sorted: priority 1 first, then priority 2

**Todo List:**
- [ ] Define the `SKILL_RESOURCES` dict with at least 15 common skills
- [ ] Implement `RoadmapGenerator` class with all methods
- [ ] Ensure output is sorted by priority ascending

**Relevant Context:** `core/models.py` (SkillGapResult, LearningRoadmap, RoadmapItem, JobRole).

**Status:** [ ] pending

---

## Sub-Task 8 — Score Calculator (`core/score_calculator.py`)

**Intent:** Produce a single 0–100 job-readiness score from 4 weighted factors.
The weights and label bands are defined here — easy to tune without touching the UI.

**Expected Outcomes:**
- `ScoreCalculator.calculate()` returns a `ReadinessScore` with all 4 sub-scores and a label
- Score is also saved as a row in `data/results/skill_gap_results.csv`

**Class: `ScoreCalculator`**
| Method | Responsibility |
|---|---|
| `__init__(self, csv_path: str)` | Store CSV path |
| `calculate(profile: UserProfile, gap: SkillGapResult, progress: list[ProgressRecord]) -> ReadinessScore` | Compute and return score |
| `save_score(score: ReadinessScore, role_title: str) -> None` | Append score snapshot to CSV |

**Score Formula (weights sum to 100):**

| Factor | Weight | How to Calculate |
|---|---|---|
| Skill match | 40% | `gap.match_percentage * 0.40` |
| Education level | 20% | Map education string to 0–20 points (see table below) |
| Project count | 20% | `min(profile.projects count, 5) / 5 * 20` (capped at 5 projects) |
| Roadmap progress | 20% | `completed_items / total_items * 20` (0 if no roadmap yet) |

**Education Level Points:**
| Level | Points |
|---|---|
| high_school | 4 |
| associate | 8 |
| bootcamp | 10 |
| self_taught | 10 |
| bachelor | 14 |
| master | 18 |
| phd | 20 |

**Score Label Bands:**
| Score | Label |
|---|---|
| 0–39 | "Beginner" |
| 40–59 | "Developing" |
| 60–79 | "Ready" |
| 80–100 | "Strong" |

**CSV Row Fields:**
`timestamp, role_title, total_score, skill_score, education_score, project_score, progress_score, label`

**Todo List:**
- [ ] Implement `ScoreCalculator` with `calculate()` and `save_score()` methods
- [ ] Define `EDUCATION_POINTS` and `SCORE_LABELS` as module-level constants
- [ ] Wire CSV persistence to `storage/csv_storage.py`

**Relevant Context:** `core/models.py` (ReadinessScore, UserProfile, SkillGapResult, ProgressRecord).

**Status:** [ ] pending

---

## Sub-Task 9 — Interview Prep (`core/interview_prep.py`)

**Intent:** Generate targeted interview questions at runtime from the user's specific missing skills.
No static question bank — questions are assembled from templates + the skill name.
This keeps it dynamic without any AI API.

**Expected Outcomes:**
- `InterviewPrep.generate_questions()` returns a list of `InterviewQuestion` objects
- Questions are skill-specific and vary by question type (conceptual, practical, behavioural)
- At least 2 questions per missing skill, max 3

**Class: `InterviewPrep`**
| Method | Responsibility |
|---|---|
| `generate_questions(gap: SkillGapResult) -> list[InterviewQuestion]` | Produce questions for all missing skills |
| `_questions_for_skill(skill: str) -> list[InterviewQuestion]` | Generate 2–3 questions for one skill using templates |

**Question Templates (applied per skill):**
1. "Can you explain what {skill} is and why it is important for this role?"
2. "Describe a time you used {skill} to solve a problem. What was the outcome?"
3. "What are the most common challenges when working with {skill}?"

**Tip Templates (applied per skill):**
1. "Focus on fundamentals and real-world use cases of {skill}."
2. "Use the STAR method (Situation, Task, Action, Result) and mention {skill} specifically."
3. "Show awareness of trade-offs and limitations of {skill}."

**Todo List:**
- [ ] Implement `InterviewPrep` class with both methods
- [ ] Define question and tip template lists as module-level constants
- [ ] Return an empty list if no missing skills exist

**Relevant Context:** `core/models.py` (InterviewQuestion, SkillGapResult).

**Status:** [ ] pending

---

## Sub-Task 10 — Progress Tracker (`core/progress_tracker.py`)

**Intent:** Let users mark roadmap skills as not started, in progress, or completed.
Progress is persisted in JSON so it survives browser refreshes.

**Expected Outcomes:**
- `ProgressTracker` loads and saves progress records for each skill in the roadmap
- Users can update any skill's status
- `get_completion_rate()` returns a 0.0–1.0 float used by the score calculator

**Class: `ProgressTracker`**
| Method | Responsibility |
|---|---|
| `__init__(self, storage_path: str)` | Load existing progress from JSON |
| `initialise_from_roadmap(roadmap: LearningRoadmap) -> None` | Seed progress records for new roadmap skills |
| `update_status(skill: str, status: str) -> None` | Change a skill's status and save |
| `get_all_records() -> list[ProgressRecord]` | Return all progress records |
| `get_completion_rate() -> float` | `completed_count / total_count` (0.0 if empty) |
| `_save() -> None` | Persist to JSON |
| `_load() -> None` | Load from JSON |

**Status values:** `"not_started"`, `"in_progress"`, `"completed"`

**Todo List:**
- [ ] Implement `ProgressTracker` class with all methods
- [ ] On `initialise_from_roadmap`, do not overwrite status of skills already tracked
- [ ] Wire `_save` / `_load` to `storage/json_storage.py`

**Relevant Context:** `core/models.py` (ProgressRecord, LearningRoadmap), `storage/json_storage.py`.

**Status:** [ ] pending

---

## Sub-Task 11 — Streamlit UI Layer (`ui/` + `app.py`)

**Intent:** Build the Streamlit pages that call the core business logic.
The UI layer must contain NO business logic — it only calls `core/` classes and renders results.

**Expected Outcomes:**
- `app.py` renders a sidebar navigation to all 7 pages
- Each page module has a single `render()` function
- All Streamlit session state is initialised in `app.py` on first run

**Pages and Responsibilities:**

### `app.py`
- Initialise session state keys: `profile`, `role`, `gap_result`, `roadmap`, `score`, `questions`, `progress_tracker`
- Instantiate all `core/` class objects once (stored in session state)
- Sidebar with page navigation using `st.sidebar.radio`

### `ui/pages/page_profile.py` — "My Profile"
- Form: name, education level (selectbox), skills (text area, comma-separated), target role (dropdown + custom option)
- On submit: calls `ProfileManager.create_profile()`
- Shows current profile summary if already exists

### `ui/pages/page_role_selection.py` — "Target Role"
- Selectbox of base roles + "Custom" option
- If Custom: text input for role title + text area for required skills
- Calls `RoleManager.get_role()` or `RoleManager.create_custom_role()`
- Saves selected `JobRole` to session state

### `ui/pages/page_skill_gap.py` — "Skill Gap Analysis"
- Button: "Run Analysis"
- On click: calls `SkillGapAnalyzer.analyze()` and `save_result()`
- Shows matched skills (green), missing skills (red), extra skills (blue), match %

### `ui/pages/page_roadmap.py` — "Learning Roadmap"
- Calls `RoadmapGenerator.generate()` using current gap result
- Displays roadmap items sorted by priority with resources
- Calls `ProgressTracker.initialise_from_roadmap()`

### `ui/pages/page_score.py` — "Readiness Score"
- Button: "Calculate Score"
- Calls `ScoreCalculator.calculate()` and `save_score()`
- Displays total score as `st.metric`, sub-scores as a bar breakdown, label badge

### `ui/pages/page_interview_prep.py` — "Interview Prep"
- Calls `InterviewPrep.generate_questions()` from current gap result
- Renders each question in a `st.expander` with the tip inside

### `ui/pages/page_progress.py` — "Progress Tracker"
- For each roadmap skill: show current status + a `st.selectbox` to update it
- On change: calls `ProgressTracker.update_status()`
- Shows overall completion rate as a progress bar

### `ui/components.py` — Shared helpers
- `show_skill_badge(skill: str, colour: str)` — renders a coloured skill tag using `st.markdown`
- `show_score_bar(label: str, value: float, max_val: float)` — renders a mini progress bar

**Todo List:**
- [ ] Implement `app.py` with session state init and sidebar navigation
- [ ] Implement each page module with a `render()` function
- [ ] Implement `ui/components.py` shared helpers
- [ ] Ensure no business logic lives in the UI layer

**Relevant Context:** All `core/` classes. `app.py` is the Streamlit entry point.

**Status:** [ ] pending

---

## Sub-Task 12 — Unit Tests (`tests/`)

**Intent:** Verify all business logic works correctly in isolation.
Tests run against core classes only — no Streamlit, no real file I/O (use tmp paths or monkeypatching).

**Expected Outcomes:**
- All test files pass with `pytest tests/`
- Coverage includes happy path + at least one edge/error case per class

**Test Cases:**

### `test_profile_manager.py`
- Create a valid profile and verify all fields saved correctly
- Update skills and verify the change persists (reloads from JSON)
- Raise `ValueError` when `education_level` is invalid
- Raise `ValueError` when `name` is empty

### `test_role_manager.py`
- `get_all_role_titles()` returns a list of strings
- `get_role("Data Scientist")` returns correct `JobRole` with expected skills
- `get_role("NonExistent")` returns `None`
- `create_custom_role("My Role", ["Python"])` returns `JobRole` with `is_custom=True`

### `test_skill_gap_analyzer.py`
- All required skills present → `match_percentage` is 100.0, `missing_skills` is empty
- No skills present → `match_percentage` is 0.0, all skills in `missing_skills`
- Partial match → correct split of matched/missing/extra
- Case-insensitive: "python" matches "Python"

### `test_score_calculator.py`
- Perfect profile (all skills, PhD, 5 projects, 100% progress) → score close to 100
- Empty profile (no skills, high school, 0 projects, 0% progress) → score close to 4
- Education mapping: verify each level maps to correct points
- Label bands: 35 → "Beginner", 55 → "Developing", 70 → "Ready", 85 → "Strong"

### `test_roadmap_generator.py`
- Missing 3 skills → roadmap has 3 items
- Items sorted by priority (priority 1 first)
- Unknown skill gets generic fallback resources
- Empty missing skills → empty roadmap

### `test_interview_prep.py`
- 2 missing skills → at least 4 questions returned (2 per skill)
- Each question references the skill name in the text
- No missing skills → empty list

### `test_progress_tracker.py`
- Initialise from roadmap with 4 skills → 4 records with `"not_started"` status
- Update one skill to `"completed"` → `get_completion_rate()` returns 0.25
- Re-initialise from same roadmap does not overwrite existing statuses

**Todo List:**
- [ ] Write all test files above using `pytest` and `tmp_path` fixture for file paths
- [ ] Ensure all tests pass with `pytest tests/ -v`

**Relevant Context:** All `core/` and `storage/` modules.

**Status:** [ ] pending

---

## Business Logic Flow

```
User fills profile
      |
      v
Role selected (base or custom)
      |
      v
SkillGapAnalyzer.analyze(user_skills, role)
      |
      v
RoadmapGenerator.generate(gap_result, role)
      |
      v
ProgressTracker.initialise_from_roadmap(roadmap)
      |
      v
User marks progress in tracker
      |
      v
ScoreCalculator.calculate(profile, gap_result, progress_records)
      |
      v
InterviewPrep.generate_questions(gap_result)
```

---

## Input Validation Summary

| Input | Rule |
|---|---|
| `name` | Non-empty, max 100 chars |
| `skills` | List of non-empty strings, no duplicates, max 50 |
| `education_level` | Exact match against 7 allowed values |
| `target_role` | Non-empty string |
| `project.title` | Non-empty string |
| `custom role skills` | At least 1 skill required |
| `progress status` | Must be one of: `not_started`, `in_progress`, `completed` |

All validation raises `ValueError` with a user-readable message. The Streamlit UI catches `ValueError` and displays it with `st.error()`.

---

## Exception Handling Summary

| Scenario | Handler |
|---|---|
| JSON file missing on first run | `json_storage.load_json` returns `{}` silently |
| CSV file missing on first run | `csv_storage.read_csv_rows` returns `[]` silently |
| Profile not created, user jumps to Skill Gap page | UI shows `st.warning("Please create your profile first.")` |
| Role not selected, user jumps to Skill Gap page | UI shows `st.warning("Please select a target role first.")` |
| Invalid input in forms | `ValueError` caught by UI, displayed with `st.error()` |
| Empty missing skills going into interview prep | `InterviewPrep` returns empty list; UI shows "No skill gaps — you are ready for interviews!" |

---

## CSV / JSON Storage Design

### `data/profiles/profile.json`
Stores a single serialised `UserProfile` dict. Overwritten on every save.

### `data/progress/progress.json`
Stores a list of serialised `ProgressRecord` dicts. Overwritten on every save.

### `data/results/skill_gap_results.csv`
Append-only. One row per analysis run. Columns:
`timestamp, role_title, matched_skills, missing_skills, match_percentage`

### `data/results/score_history.csv`
Append-only. One row per score calculation. Columns:
`timestamp, role_title, total_score, skill_score, education_score, project_score, progress_score, label`

---

## Step-by-Step Implementation Order

1. Sub-Task 1 — Scaffold (folders, stubs, requirements.txt)
2. Sub-Task 2 — Data models (`core/models.py`)
3. Sub-Task 3 — Storage layer (`storage/`)
4. Sub-Task 4 — Role manager (`core/role_manager.py`)
5. Sub-Task 5 — Profile manager (`core/profile_manager.py`)
6. Sub-Task 6 — Skill gap analyzer (`core/skill_gap_analyzer.py`)
7. Sub-Task 7 — Roadmap generator (`core/roadmap_generator.py`)
8. Sub-Task 8 — Score calculator (`core/score_calculator.py`)
9. Sub-Task 9 — Interview prep (`core/interview_prep.py`)
10. Sub-Task 10 — Progress tracker (`core/progress_tracker.py`)
11. Sub-Task 11 — Streamlit UI layer (`ui/` + `app.py`)
12. Sub-Task 12 — Unit tests (`tests/`)

---

## Main User Flows to Test Manually

1. **Happy path:** Create profile → select base role → run analysis → view roadmap → update progress → calculate score → view interview questions
2. **Custom role:** Same as above but choose "Custom" role and define title + skills manually
3. **Persistence:** Complete flow → close browser → reopen → verify profile and progress loaded from files
4. **Jump navigation:** Go directly to Skill Gap page without a profile → verify warning shown
5. **Edge case:** User already has all required skills → missing_skills empty → roadmap empty → interview prep shows "ready" message
6. **Score progression:** Update progress to 100% → recalculate score → verify progress_score component increases

---

## Assumptions and Limitations

| Item | Detail |
|---|---|
| Single user | One profile.json — no multi-user, no auth |
| Static resources | Learning resources are hardcoded strings, not live links |
| No AI/LLM | Interview questions use string templates, not a language model |
| Session state | All runtime objects live in Streamlit session state; refreshing the page reloads from files |
| Skill matching | Exact string match after normalisation — no fuzzy/semantic matching |
| CSV is append-only | Old results accumulate; no deduplication or cleanup logic |
| Project skills | Projects contribute to the profile display only; they are NOT counted toward the skill-match score (only `profile.skills` is used) |
| Roadmap resources | Resources are suggestions only — app does not check if URLs are live |
| Score weights | The 4 weights (40/20/20/20) are constants and not configurable from the UI |
| Education level | Bootcamp and self-taught are treated equally in scoring |
