# Session Progress Snapshot

**Updated**: 2026-09-08
**Branch**: `001-student-management`
**Feature**: 001-student-management (Student Management System)
**Last Action**: Phase D PDF report cards complete (T046–T049) — 90 tests green, ruff clean

## Context / Goal

Multi-role Student Management System (admin/teacher/parent): student core + attendance, grades,
courses, parents/parent portal, PDF report cards, React frontend. Working through
`specs/001-student-management/tasks.md` (T001–T063).

## Important Details (rules/quirks to respect)

- **User is not a programmer** — communicate next steps in plain English.
- Python runtime is **3.14.4**; use `python -m pytest`, `python -m ruff`, `python -m alembic`,
  `python -m uvicorn`, `python -m scripts.seed` (Scripts are not on PATH). Workdir: `backend/` for
  alembic/seed/uvicorn; repo root for pytest/ruff.
- Ruff ignores configured in root `pyproject.toml`: `UP037`, `DTZ011`, `DTZ012`, `B008`
  (B008 added — FastAPI `Depends()` idiom). Target `py311`.
- **User decisions (FINAL, do not revert):**
  - `grade_level` is **free text** (up to 20 chars) — NOT a K-12 enum, NOT integers. Any label
    allowed (`"K"`, `"9"`, `"K-1"`, `"O-Level"`); input is trimmed. Decision made 2026-09-07,
    applied everywhere (models, schemas, services, migration `c4b1a9f2e8d3`, contract, docs).
    Report-card grade ORDERING will need a small sort field when reports are built (T046+) —
    free text sorts alphabetically (10 before 2).
  - Phone numbers are **text** (leading zeros/`+`/`-`).
  - Frontend: React (Vite). One `users` table. MVP-first approach (done).
- **Demo credentials** (dev DB + seed.py): admin `admin@schoolsystem.com` / `changeme123`;
  teacher `jane.smith@schoolsystem.com` / `teacher123`; parent `maria.doe@family.net` / `parent123`.
  `.local`/`school.edu` domains are rejected by email-validator — use `schoolsystem.com`/`family.net`.
- Email convention: login trims whitespace; student/teacher emails use lenient validation
  (`schemas/common.py: validate_email_lenient`, `check_deliverability=False`).
- RBAC matrix: Student CRUD = admin only (teachers/parents read-scoped); Teacher CRUD = admin only;
  Course read = admin + teacher **own courses** only (`assert_can_access_course` in `api/courses.py`);
  Course write (incl. roster PUT) = admin only. Attendance/grades later: teacher own course.
- Tests: contract in `tests/contract/`, integration in `tests/integration/`; `tests/conftest.py` uses
  `StaticPool` in-memory SQLite + `check_same_thread=False` (per-thread DB fix). TestClient WITHOUT
  context manager does NOT trigger lifespan (intentional — tests never touch dev DB). The
  `StarletteDeprecationWarning` about httpx2 in output is benign.
- Dev DB at `backend/student_management.db` is seeded (demo teacher+parent+students, plus
  user-created student Ali Khan). Run `python -m scripts.alembic upgrade head` then
  `python -m scripts.seed --demo` to rebuild (delete the .db first if needed).
- **YAML edit gotcha**: the `edit` tool matches substrings — a `CourseResponse:` oldString without
  leading spaces stripped indentation from `    CourseResponse:`. When editing indentation-sensitive
  files (openapi.yaml), match whole lines with full indent, or use a python one-liner.
- Git: no commits yet on `001-student-management` (T063 plans the first commit).

## Work State

### Completed
- Phase A foundation (config, db, models, security, auth): admin/teacher/parent login via one
  `users` table, bcrypt, JWT. Apps raise `AppNotConfiguredError` on bad config.
- Auth test fix: `StaticPool` + `check_same_thread=False`; `main.py` lifespan (deprecation-free);
  longer dev `SECRET_KEY`. seed.py calls `ensure_schema()` (create_all) first.
- **US1 student core (T020–T025) done**: schemas/student.py + enrollment.py,
  services/student_service.py, api/students.py (POST/GET list w/ filters+search/GET+PUT by id,
  POST /enrollments). 32 tests green at that point.
- **Credential/email-validator fix**: valid demo domains; docs (quickstart, openapi) updated;
  DB reseeded; real login verified (200 ok/trimmed-spaces, 401 unknown).
- MVP manually validated by user via `/docs` (login, student POST/GET/PUT). Tasks T001–T025 marked.
- **US6 Teachers & Courses (T026–T030) done**:
  - `schemas/teacher.py`, `schemas/course.py` (+ `CourseRosterUpdate`), `schemas/common.py`.
  - `services/teacher_service.py`, `services/course_service.py` (assign_course_students added).
  - `api/teachers.py` (GET/POST /teachers, GET /teachers/{id}, admin-only),
    `api/courses.py` (GET/POST /courses, GET/PUT /courses/{id}, GET+PUT /courses/{id}/students —
    roster PUT added to fulfill US6 "assign students to courses"; admin-only write).
  - Routers wired into `main.py`. Contract tests `tests/contract/test_teachers_courses.py` +
    integration `tests/integration/test_teachers_courses_flow.py`. **45 tests pass, ruff clean.**
  - openapi.yaml now documents PUT /courses/{id}/students + CourseRosterUpdate (YAML re-validated);
    quickstart.md documents the roster endpoint. tasks.md T026–T030 marked.
- **grade_level → free text (2026-09-07)**: removed K-12 enum + DB check constraints, widened
  `String(2)` → `String(20)` on students & courses (migration `c4b1a9f2e8d3`); schemas use plain
  `str` (min 1/max 20, stripped); contract/data-model/quickstart updated. Dev DB migrated in place
  (stamped then upgraded — records preserved). **46 tests pass, ruff clean.**
- **US4 Attendance (T031–T034) DONE**: `schemas/attendance.py` (AttendanceCreate w/ records list
  + no-future-date guard), `services/attendance_service.py` (upsert per student/course/date,
  roster-membership + duplicate checks), `api/attendance.py` —
  POST `/api/v1/attendance` (mark, own course for teachers, admin any, `marked_by` user.teacher_id),
  GET `/api/v1/attendance/{course_id}?date=`, GET `/api/v1/students/{student_id}/attendance`
  (teacher scoped to own students). Moved `assert_can_access_course` into `api/deps.py`.
  `make_auth_headers` gained `teacher_id`/`parent_id`. **55 tests pass, ruff clean.**
- **US5 Grades (T035–T038) DONE**: `schemas/grade.py` (GradeCreate: grade_value 0–100 float,
  assignment_type enum, date_due >= date_assigned validator), `services/grade_service.py`
  (record_grade sets `date_graded = max(today, date_due)` to satisfy the DB check constraint,
  roster-membership + student-exists checks), `api/grades.py` —
  POST `/api/v1/grades` (own course teachers / any admin), GET `/api/v1/students/{id}/grades`
  (+ `courseId` filter, teacher scoped to own students), GET `/api/v1/courses/{id}/grades`.
  Reused `get_student_or_404`/`student_in_teacher_courses` from attendance_service. Router wired
  in main.py. **63 tests pass (55 + 8 new), ruff clean** (also auto-fixed 3 pre-existing I001
  import-sort issues in `backend/alembic/` so the root `ruff check .` gate is green).

### Active / Next
- **Phase D — PDF report cards (T046–T049) DONE (2026-09-08)**: `report_service.py` (ReportLab),
  `GET /api/v1/reports/{student_id}` → `application/pdf`. Course rows ordered A-Z by NAME in the report
  (because `grade_level` free text sorts "10" before "2"); a real academic order would need a future
  numeric sort field on courses. **90 tests pass, ruff clean.**
- Next: React frontend (T050+), then Phase F final checks.

### Login-accounts + US8 Parent Portal (2026-09-08)
- User chose **FLEXIBLE passwords**: optional at creation, retro-active endpoint for existing records.
- **T042a**: optional `password` (min 8) field on `TeacherCreate` and `ParentCreate`. When provided, the
  service creates the linked `users` row in the same transaction (role teacher/parent,
  `teacher_id`/`parent_id` FK). Fixed a subtle bug: `db.flush()` is required before reading
  `parent.parent_id`/`teacher.teacher_id`, otherwise the User row gets a NULL link and the portal
  ownership check 403s.
- **T042b**: `POST /api/v1/teachers/{teacher_id}/account` + `POST /api/v1/parents/{parent_id}/account`
  (admin-only, body `{ "password": "..." }`). Uses the entity's email; 404 unknown id (strip-guard),
  400 if a login already exists. New `services/account_service.py` +
  `schemas/account.py` (AccountCreate/Detail/Response). Messages: "Teacher login created" /
  "Parent login created".
- **US8 Portal (T043–T045)**: `GET /api/v1/parents/{parent_id}/portal` — parent-role only, user must
  be the owner (`user.parent_id == parent.parent_id`, else 403), 404 unknown parent. Service
  `get_parent_with_children` eager-loads children + attendance + grades
  (`selectinload(Parent.students).selectinload(Student.attendance_records/grades)`).
  `schemas/parent.py` gained PortalChild/PortalParent/ParentPortal; response shape per openapi
  `ParentPortal` ref.
- Tests: `tests/contract/test_accounts.py` (9), `tests/contract/test_portal.py` (4),
  `tests/integration/test_portal_flow.py` (full journey: teacher no-pw → account → login → teaches →
  attendance + grade → parent created WITH password → parent login → portal shows child data → wrong
  password still 401). Ran full suite twice: **85 tests pass, ruff clean.**
- Docs: openapi.yaml — account endpoints under teachers/parents, optional `password` on create schemas,
  `AccountCreate`/`AccountDetail`/`AccountResponse` components (YAML re-validated with
  `yaml.safe_load`). quickstart.md updated. tasks.md T043–T045 + T042a/T042b marked done.
- **Give a login to hassan/any existing teacher**: call `POST /api/v1/teachers/{teacher_id}/account`
  (or create future teachers with a `password`). Same for parents.

### Bug fix (2026-09-08) — GET /courses/{id} 500 → 404
- User hit **500 "Internal Server Error"** (21-byte text/plain) on `GET /api/v1/courses/{course_id}` with a
  copy-pasted id. Root cause: `get_course_with_reads()` in `services/course_service.py` had NO guard —
  malformed id → `ValueError` → 500; unknown id → `None` → `AttributeError` in
  `assert_can_access_course`/`CourseDetail.model_validate` → 500. Sibling endpoints all use the guarded
  `get_course_or_404`.
- **Fix**: `get_course_or_404` now `strip()`s the incoming id (handles paste-with-newline), and
  `get_course_with_reads` reuses `get_course_or_404` before eager-loading students. Added contract test
  `test_get_course_404_for_unknown_or_malformed_id` (unknown uuid→404, non-uuid→404, valid id + %0A→200,
  unknown id + whitespace→404). **64 tests pass, ruff clean.**
- **Related gap noted**: `POST /teachers` does NOT create a `users` login row → teachers added via the API
  cannot log in (only seed.py demo teachers have passwords). User said no password needed for now — revisit
  if a "create teacher account" endpoint is wanted.
- **US7 Parents (T039–T042) DONE (2026-09-08)**: `schemas/parent.py` (ParentCreate: name/email/phone
  required, lenient email validator, phone = free text with student PHONE_PATTERN, optional student_ids),
  `services/parent_service.py` (create w/ duplicate-email check + link-students validation, get_parent_or_404
  with strip guard → 404 no-500, list_parent_students), `api/parents.py` — GET/POST `/api/v1/parents` +
  GET `/api/v1/parents/{id}/students`, all admin-only. Router wired in main.py. Contract tests
  `tests/contract/test_parents.py` + integration `tests/integration/test_parents_flow.py`. **73 tests pass,
  ruff clean.** Same caveat as teachers: POST /parents does NOT create a parent login (portal T043–T045 next).

### Blocked
- None.

## Conversation Log (2026-09-08, after US8 build)

- **Q: "which things will be shown to a teacher?"** — Asked what a teacher sees/does in the system.
  Answer given (verified against code guards): teachers can READ students (list/search/get) and their OWN
  courses + rosters; they can WRITE attendance + grades for their OWN courses only
  (`assert_can_access_course` → 403 otherwise); everything else (student/teacher/course/parent
  management, portal) is admin-only; portal is parent-only. Endpoint guards: `staff_only =
  require_roles("admin","teacher")` in students.py/courses.py/attendance.py/grades.py; courses list is
  auto-scoped to `own_teacher_id` for teachers. Report cards (T046+, not built) will be teacher-tool too.
- **Q: "how to create a parent or give login to hassan via POST/teachers"** — Clarified that
  `POST /teachers` only creates a NEW teacher and does NOT logify existing ones; the login endpoint is
  `POST /api/v1/teachers/{teacher_id}/account` (`{"password": "..."}`). Gave full `/docs` walkthrough:
  login as admin → GET /teachers → copy id → POST account → 201 "Teacher login created"; create parent with
  optional `password` via POST /parents; retroactive parent login via POST /parents/{id}/account.
- **Support ticket: user got 422 on `POST /api/v1/parents`** after pasting the example body with the
  literal placeholder `"student_ids": ["<a_student_id>"]`. Root cause: `<a_student_id>` is not a valid
  uuid → pydantic 422 for the whole request. Fix: use a REAL id from `GET /api/v1/students`, or omit the
  `student_ids` field entirely (defaults to empty list → parent created with no children). Asked user to
  share the exact error detail if it persists. NO code bug — request-shape issue.
- **Q: "why student id with square brackets?"** — Explained `[]` = JSON list/array = "this field can hold
  MORE THAN ONE id" because a parent may have multiple children. One child → one id in the list; two
  children → two ids; omit → same as empty list.
- **User insight acknowledged**: "it is not mandatory that a parent has a single child in the school —
  maybe they have 2". The design ALREADY supports this: one parent ↔ many students (many-to-many via
  `parent_students`), `student_ids` is an array, and the portal returns ALL linked children each with
  their own attendance/grades.
- **Gap surfaced + proposal (PENDING user decision)**: children can only be linked to a parent at
  CREATION time — there is no "edit parent's children later" endpoint. Proposed a new admin-only
  `PUT /api/v1/parents/{parent_id}/students` (`{"student_ids": [...]}`) + tests + docs (swap/create
  pattern like `PUT /courses/{id}/students`). User has not yet said yes. Do NOT build until confirmed.
- Status at close of this conversation: **90 tests pass, ruff clean.** Phase D PDF reports (T046–T049)
  complete: report cards order courses A-Z by name; grade_level stays free text.

## Relevant Files (absolute)
- `C:\Users\Naqeeb\Desktop\management\backend\src\student_management\main.py` — app + lifespan + routers
- `C:\Users\Naqeeb\Desktop\management\backend\src\student_management\api\{students,teachers,courses,auth,attendance,grades,parents,reports,administrators}.py`
- `C:\Users\Naqeeb\Desktop\management\backend\src\student_management\schemas\{student,enrollment,teacher,course,auth,common,attendance,grade,parent,account}.py`
- `C:\Users\Naqeeb\Desktop\management\backend\src\student_management\services\{student_service,teacher_service,course_service,attendance_service,grade_service,parent_service,account_service,report_service}.py`
- `C:\Users\Naqeeb\Desktop\management\backend\src\student_management\models\` — student, teacher, course, enums (statuses/roles; GradeLevel enum removed)
- `C:\Users\Naqeeb\Desktop\management\tests\conftest.py` — db/client/make_auth_headers fixtures
- `C:\Users\Naqeeb\Desktop\management\tests\contract\test_{students,teachers_courses,attendance,grades,parents,accounts,portal,reports}.py`, `tests\integration\test_*_flow.py`
- `C:\Users\Naqeeb\Desktop\management\specs\001-student-management\tasks.md` — task status (T001–T049 done)
- `C:\Users\Naqeeb\Desktop\management\specs\001-student-management\contracts\openapi.yaml` — teachers/courses/attendance/grades/parents/portal/reports documented
- `C:\Users\Naqeeb\Desktop\management\backend\scripts\seed.py` — demo credentials + data