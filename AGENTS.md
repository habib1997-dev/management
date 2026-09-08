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
- PENDING USER DECISION: proposal to change a parent's children AFTER creation — USER APPROVED 2026-09-08, now BUILT: `PUT /api/v1/parents/{parent_id}/students` (admin-only, swap pattern like course roster).
- 2026-09-08 (build session): First git commit created (e4598f5). Backend housekeeping DONE — PUT /parents/{id}/students (edit children), course max_students capacity enforced (400 "Course capacity exceeded"), admin account management (GET /administrators/users + PUT /administrators/users/{id} {active?, password?}), GET /students/{id}/parents lookup. **100 tests pass, ruff clean.**
- 2026-09-08 (frontend session): Phase E React frontend started — T050 scaffold (Vite+React18+react-router 6, JWT client, proxy /api→:8000), T051 login, T052 students, T053 teachers+courses, T056 parents ALL DONE. `npm run build` passes; live smoke test through Vite proxy OK. Remaining: T054/T055 (teacher attendance+grades), T057/T058 (parent portal + PDF download).
- 2026-09-08 (soft-delete session): "Remove" = **deactivate/restore** (soft delete, chosen by user). New admin endpoints `PUT /teachers/{id}` + `PUT /parents/{id}` `{"status": bool}` (auto-disables the linked login); guards: inactive teacher → 400 on course assign, inactive parent → 403 portal, inactive student → 400 on attendance/grades. Frontend Deactivate/Restore buttons + student-name search box in Linked-children + course-roster pickers; course teacher dropdown hides inactive teachers. **110 tests pass, ruff clean**, `npm run build` OK. No DELETE endpoints exist — records are never erased.
- 2026-09-08 (edit-panel session): "Edit" panels replace Deactivate buttons. `PUT /teachers/{id}` and `PUT /parents/{id}` now also accept `name/email/subjects_taught` / `name/email/phone` (partial, dup-email 400, format-validated) alongside `status`; login still syncs with status. Students/Teachers/Parents each get one **Edit** button → panel pre-fills profile fields + an "Account active" checkbox (deactivate/restore folded in); Parents' panel also edits linked children. **119 tests pass, ruff clean**, `npm run build` OK. New: `tests/contract/test_profile_edit.py`.
- NEXT: teacher attendance (T054) + grades (T055) screens; then parent portal (T057) + report PDF button (T058); Phase F final checks (T059–T063).

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
