# management Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-09-07

## Active Technologies

- NEEDS CLARIFICATION - Determine target language/framework (e.g., Python FastAPI, Node.js/Express, or Java Spring Boot) + NEEDS CLARIFICATION - ORM (e.g., SQLAlchemy, TypeORM, Hibernate), validation library, authentication middleware (001-student-management)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

NEEDS CLARIFICATION - Determine target language/framework (e.g., Python FastAPI, Node.js/Express, or Java Spring Boot): Follow standard conventions

## Recent Changes

- 001-student-management: Added NEEDS CLARIFICATION - Determine target language/framework (e.g., Python FastAPI, Node.js/Express, or Java Spring Boot) + NEEDS CLARIFICATION - ORM (e.g., SQLAlchemy, TypeORM, Hibernate), validation library, authentication middleware

<!-- MANUAL ADDITIONS START -->

## Session Resumption

If resuming work on 001-student-management, **read `history/session-progress.md` FIRST** for the exact state (completed files, remaining files, next steps). It is the single source of truth for in-progress work.

### Current Status (2026-09-07)
- Spec expanded with 5 high-value additions: attendance, grades, courses, parents/parent portal, reports (PDF report cards)
- Roles: admin, teacher, parent
- Tech stack (resolved): Python 3.11 + FastAPI + SQLAlchemy + PostgreSQL 15, pydantic, JWT, pytest+httpx

### Build Status (2026-09-07)
- US1 student core (T020–T025) — DONE, user-validated via /docs. US6 teachers & courses (T026–T030) — DONE (45 tests, ruff clean; added PUT /courses/{id}/students roster endpoint beyond contract). MVP checkpoint passed.
- grade_level is now FREE TEXT (max 20 chars) — no more K-12 enum/check-constraints (user decision; migration c4b1a9f2e8d3 applied to dev DB). Report-card grade ordering will need a small sort field when reports are built (T046+).
- US4 attendance (T031–T034) — DONE (55 tests, ruff clean; teacher marks own courses, upsert per student/course/date, admin any course, students must be on course roster).
- US5 grades (T035–T038) — DONE (63 tests, ruff clean; POST /api/v1/grades 0–100 validation + assignment_type enum + date order check, teacher own courses / admin any, student must be on roster; GET student grades with courseId filter / GET course grades; date_graded = max(today, date_due) satisfies DB check constraint).
- 2026-09-08: fixed GET /courses/{id} 500→404 bug (get_course_with_reads now guards via get_course_or_404; strip() on ids). US7 parents (T039–T042) — DONE (73 tests, ruff clean; GET/POST /parents + GET /parents/{id}/students, admin-only, link student_ids on create, duplicate-email check, strip-guard 404s).
- 2026-09-08 (later): login accounts for teachers/parents + US8 parent portal — DONE. Optional `password` (min 8) accepted on POST /teachers and POST /parents (creates the linked `users` row; requires `db.flush()` before reading the new PK). Retroactive: POST /teachers/{id}/account + POST /parents/{id}/account (admin-only; 404 strip-guard, 400 if login already exists). Portal: GET /parents/{id}/portal (parent-role, own children only → else 403; 404 unknown; eager-loads students + attendance + grades). New files: schemas/account.py, services/account_service.py, api adds. **85 tests pass, ruff clean.** openapi.yaml + quickstart updated.
- DEV RUN: note schoolsystem.com demo credential domains (not .local). grade_level stays text; phones stay text.
- 2026-09-08 supports/Q&A: teachers see/do read-students + own-course attendance/grades only (403 outside own courses); parent `student_ids` is a LIST (parents may have 2+ children); a 422 from POST /parents is user-error if they paste a literal placeholder id — use a real uuid or omit the field.
- PENDING USER DECISION (2026-09-08): proposed admin-only `PUT /api/v1/parents/{parent_id}/students` to change a parent's child list AFTER creation (currently only settable at create). NOT built yet — do not build until the user confirms.
- NEXT: Phase D PDF reports (T046–T049) — DONE (2026-09-08). Report card orders courses A-Z by NAME (grade_level stays free text; a numeric sort field would be needed only for a strict academic order).

### Updated Files (done)
- `specs/001-student-management/spec.md` — 8 user stories, 14 FRs, 8 SCs
- `specs/001-student-management/data-model.md` — entities: Student, Enrollment, Teacher, Course, Parent, Attendance, Grade
- `specs/001-student-management/contracts/openapi.yaml` — new endpoints for teachers, courses, attendance, grades, parents, portal, reports (PDF); YAML validated

### Spec Docs Status
- `specs/001-student-management/` — all docs complete: spec (5 additions), data-model (7 entities), contracts/openapi.yaml (teachers/courses/attendance/grades/parents/portal/reports), quickstart, plan, research, checklists/requirements. YAML re-validated 2026-09-07 after adding PUT /courses/{id}/students.

### Implementation Status (see tasks.md)
- T001–T049 all done (auth foundation, US1 student core, US6 teachers/courses, US4 attendance, US5 grades, US7 parents, login accounts, US8 portal, Phase D PDF reports — 90 tests, ruff clean).
- Remaining: Phase E React frontend (T050+) and Phase F.

<!-- MANUAL ADDITIONS END -->
