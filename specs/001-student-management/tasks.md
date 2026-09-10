# Tasks: 001-student-management (Student Management System)

**Input**: Design documents from `specs/001-student-management/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml
**Tests**: Included — TDD/test-first is required by the constitution.

**Organization**: Tasks grouped into 6 phases (A-F). Phases are NOT user-story independent; they are dependency-ordered as the user requested.

**Decisions locked for this build** (2026-09-07):
- Frontend framework: **React**
- Login model: **one `users` table** with `role` (admin/teacher/parent)
- Delivery: **MVP-first** (stop after student core for user review)
- Student search: contract updated — `GET /api/v1/students?search=` added

**Note (2026-09-08)**: All Phase A–D tasks (T001–T049) DONE and committed (git `e4598f5`).
Backend housekeeping beyond the task list added in that commit: `PUT /parents/{id}/students`
(edit children), course `max_students` enforcement, `GET/PUT /administrators/users`, and
`GET /students/{id}/parents`. Openapi.yaml + quickstart.md document them. Remaining work is
Phase E (React) + Phase F below.

**Added 2026-09-08 (soft-delete / deactivate)**: `PUT /teachers/{id}` + `PUT /parents/{id}`
(`{"status": bool}`, syncs the linked login) and guards — inactive teacher can't be assigned
to courses (400), inactive parent denied portal (403), inactive student can't get new
attendance/grades (400). Frontend: Deactivate/Restore buttons + student-name search in the
Linked-children and course-roster pickers. `tests/contract/test_deactivate.py` (10 tests).
**110 tests pass, ruff clean.**

**Added 2026-09-08 (profile editing / "Edit" panels)**: the same PUT endpoints now accept the
person's profile fields too — teachers `name/email/subjects_taught`, parents `name/email/phone`
(optional, partial updates; duplicate-email 400; format-validated). Frontend: each screen
(Students, Teachers, Parents) uses a single **Edit** button whose panel pre-fills the fields
plus an "Account active" checkbox (deactivate/restore folded in — standalone Deactivate buttons
removed). Parents' Edit panel also edits linked children. `tests/contract/test_profile_edit.py`
(9 tests). **119 tests pass, ruff clean.**

**Completed 2026-09-08 (Phase E teacher + parent screens, T054/T055/T057/T058)**: Teacher
**Attendance** screen (pick course + date, tick present/absent/late/excused per student) and
**Grades** screen (pick course, grade 0–100, type quiz/test/homework/final, dates) — both list the
teacher's own courses via `GET /courses`. Parent **Portal** page shows each linked child's
attendance + grades with a **"Download report card (PDF)"** button. Backend additions to support
the portal: login response now includes `teacher_id`/`parent_id`; new
`GET /reports/portal/{student_id}` lets a parent download their own child's PDF (403 otherwise).
**123 tests pass, ruff clean, `npm run build` OK.**

**Format**: `- [ ] [TaskID] [P?] [Story?] Description (Size/Blocked-by)`

---

## Phase A — Database models & migrations (data storage)

- [x] T001 Create `backend/` project structure (`backend/src/models/`, `backend/src/services/`, `backend/src/api/`, `backend/src/schemas/`) (S, blocked by: none)
- [x] T002 [P] Add dependencies `backend/requirements.txt`, `.env.example`, `backend/src/config.py` (S, none)
- [x] T003 Connect database (PostgreSQL prod / SQLite dev) — `backend/src/db.py` (M, T001)
- [x] T004 Set up Alembic migrations — `backend/alembic.ini`, `backend/alembic/` (M, T001)
- [x] T005 Student model — `backend/src/models/student.py` (M, T003)
- [x] T006 Enrollment model — `backend/src/models/enrollment.py` (S, T003)
- [x] T007 Teacher model — `backend/src/models/teacher.py` (S, T003)
- [x] T008 Course model — `backend/src/models/course.py` (S, T003)
- [x] T009 Parent model — `backend/src/models/parent.py` (S, T003)
- [x] T010 Attendance model — `backend/src/models/attendance.py` (S, T003)
- [x] T011 Grade model — `backend/src/models/grade.py` (S, T003)
- [x] T012 Relationships + constraints across all models (FKs, uniqueness, enums) (M, T005-T011)
- [x] T013 Run initial migration so all tables exist (M, T012)
- [x] T014 [P] Model tests — `tests/unit/test_models.py` (M, T005)

**Checkpoint**: All 8 tables exist and model tests pass.

## Phase B — Login + roles (JWT/RBAC)

- [x] T015 User account model (email, password_hash, role, link to teacher/parent) + migration (M, T012)
- [x] T016 Login endpoint `POST /api/v1/auth/login` issuing JWT (M, T015)
- [x] T017 Password hashing (bcrypt) (S, T015)
- [x] T018 Role guards admin/teacher/parent — `backend/src/api/deps.py` (M, T016)
- [x] T019 [P] Auth + RBAC tests — `tests/integration/test_auth.py` (M, T018)

**Checkpoint**: Login works for all 3 roles; role guards reject wrong-role access.

## Phase C — API endpoints (by feature)

### US1 — Student enrollment (P1, MVP)

- [x] T020 [P] [US1] Contract tests for student endpoints — `tests/contract/test_students.py` (M, T018)
- [x] T021 [US1] Enroll student `POST /api/v1/students` + service (M, T020)
- [x] T022 [US1] List students `GET /api/v1/students` (filters: gradeLevel, active, search) (M, T020)
- [x] T023 [US1] View + update `GET`/`PUT /api/v1/students/{student_id}` (M, T020)
- [x] T024 [US1] `POST /api/v1/enrollments` (S, T021)
- [x] T025 [US1] Integration test: enroll → search → appears in list (M, T021-T024)

**CHECKPOINT MVP**: Stop. User reviews enrollment/list/search/update flows.

### US6 — Teachers & courses

- [x] T026 [P] [US6] Contract tests for teacher/course endpoints — `tests/contract/test_teachers_courses.py` (M, T018)
- [x] T027 [US6] Teachers `GET`/`POST /api/v1/teachers`, `GET /api/v1/teachers/{id}` (M, T026)
- [x] T028 [US6] Courses `GET`/`POST /api/v1/courses` (M, T026)
- [x] T029 [US6] `GET`/`PUT /api/v1/courses/{id}` + `GET /api/v1/courses/{id}/students` (M, T028)
- [x] T030 [US6] Integration test: course + teacher + students (M, T027-T029)

### US4 — Attendance

- [x] T031 [P] [US4] Contract tests for attendance endpoints — `tests/contract/test_attendance.py` (M, T018)
- [x] T032 [US4] Mark attendance `POST /api/v1/attendance` (teacher, own course only) (M, T031)
- [x] T033 [US4] View `GET /api/v1/attendance/{course_id}` + `GET /api/v1/students/{id}/attendance` (M, T031)
- [x] T034 [US4] Integration test (M, T032-T033)

### US5 — Grades

- [x] T035 [P] [US5] Contract tests for grade endpoints — `tests/contract/test_grades.py` (M, T018)
- [x] T036 [US5] Record grade (0-100 validation) `POST /api/v1/grades` (M, T035)
- [x] T037 [US5] View `GET /api/v1/students/{id}/grades` + `GET /api/v1/courses/{id}/grades` (M, T035)
- [x] T038 [US5] Integration test (M, T036-T037)

### US7 — Parents

- [x] T039 [P] [US7] Contract tests for parent endpoints — `tests/contract/test_parents.py` (M, T018)
- [x] T040 [US7] Parents `GET`/`POST /api/v1/parents` + link to students (M, T039)
- [x] T041 [US7] `GET /api/v1/parents/{id}/students` (S, T040)
- [x] T042 [US7] Integration test (M, T040-T041)
- [x] T042a [US7/8] Optional `password` on `POST /teachers` + `POST /parents` (creates login account) (M, T042)
- [x] T042b [US7/8] `POST /teachers/{id}/account` + `POST /parents/{id}/account` (give an existing teacher/parent a login) (M, T042a)

### US8 — Parent portal

- [x] T043 [P] [US8] Contract test for portal endpoint — `tests/contract/test_portal.py` (M, T018)
- [x] T044 [US8] `GET /api/v1/parents/{id}/portal` (own children only; 403 otherwise) (M, T043)
- [x] T045 [US8] Integration test: portal data + access-denied (M, T044)

## Phase D — PDF report cards

- [x] T046 [P] Report PDF tests (M, T018)
- [x] T047 Build PDF service (ReportLab) — `backend/src/services/report_service.py` (M, T046)
- [x] T048 `GET /api/v1/reports/{student_id}` returning `application/pdf` (M, T047)
- [x] T049 Validate generated PDF content (S, T048)

## Phase E — React frontend

- [x] T050 [P] Frontend scaffold — `frontend/` (React + Vite, router, API client) (M, none)
- [x] T051 Login screen (all 3 roles) (M, T050)
- [x] T052 [P] Admin: student screens (list w/ search + enroll + edit) (M, T051)
- [x] T053 [P] Admin: teachers + courses screens (M, T051)
- [x] T054 [P] Teacher: attendance screen (M, T051)
- [x] T055 [P] Teacher: grades screen (M, T051)
- [x] T056 [P] Admin: parents screens (M, T051)
- [x] T057 Parent: portal page (child's grades, attendance, enrollment) (M, T051)
- [x] T058 Report-card PDF download button (S, T057)

## Phase F — Final quality check

- [ ] T059 Full test suite green (`pytest`) (M, all)
- [ ] T060 Lint clean (`ruff check .`) (S, all)
- [ ] T061 Coverage check (S, T059)
- [ ] T062 Quickstart steps validated end-to-end (M, T059)
- [ ] T063 Commit the finished feature (S, T059-T062)

---

## Dependencies & Execution Order

```
Phase A → Phase B → Phase C (US1 → check → US6, US4, US5, US7, US8) → Phase D → Phase E → Phase F
```

- Phases A/B block everything.
- Within Phase C, [P]-marked tasks of different stories can run in parallel; single-dev sequential order: T021→T024→T022→T023→T025 (US1), then US6→US4→US5→US7→US8.
- Tests always FIRST, ensure they FAIL before implementation.
- MVP checkpoint after T025.

## Parallel Opportunities

- All [P] tasks across any phase touch different files → can run in parallel.
- Phase E frontend screens are independent once T051 (login) and the API contract exist.

## Implementation Strategy

1. Complete Phase A → verify model tests
2. Complete Phase B → verify auth tests
3. Complete US1 (student core) → **STOP, user validates MVP**
4. Complete US6/US4/US5/US7/US8 sequentially with tests
5. Phase D (PDF) → Phase E (React) → Phase F (final checks + commit)