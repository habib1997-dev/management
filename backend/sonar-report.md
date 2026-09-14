# SonarQube Scan Report — management-backend

- **Date:** 2026-09-14 (latest analysis `2026-09-14T23:06:40+0500`)
- **Server:** SonarQube Community 26.9.0 — `http://localhost:9000`
- **Project key:** `management-backend`
- **Dashboard:** `http://localhost:9000/dashboard?id=management-backend`
- **Quality gate:** Sonar way (explicitly selected)
- **Coverage source:** `backend/coverage.xml` (`sonar.python.coverage.reportPaths`) — migrations/scripts excluded from the coverage denominator via `sonar.coverage.exclusions`

## Quality Gate — OK

| Condition | Threshold | Actual | Status |
| --- | --- | --- | --- |
| Coverage on new code | ≥ 80% | 100.0% | OK |
| Duplicated lines on new code | ≤ 3% | 0.0% | OK |
| New violations | 0 | 0 | OK |

## Measures

| Metric | Value |
| --- | --- |
| Lines of code (ncloc) | 4 395 |
| Total lines | 5 732 |
| Statements | 2 392 |
| Comment lines | 391 |
| Test coverage | **95.8%** |
| Duplicated lines density | 0.0% |
| Cognitive complexity | 468 |
| Reliability rating | A (1.0) |
| Security rating | A (1.0) |
| Maintainability rating | A (1.0) |

## Issues — 0 open

Checked via `api/issues/search?componentKeys=management-backend&resolved=false` (`ps=1`, facets by type + severity).

| Type | Count | Severity | Count |
| --- | --- | --- | --- |
| Code smells | 0 | INFO | 0 |
| Bugs | 0 | MINOR | 0 |
| Vulnerabilities | 0 | MAJOR | 0 |
| Security hotspots | 0 | CRITICAL | 0 |
|  |  | BLOCKER | 0 |

## Recent Analyses

| Date | Quality gate |
| --- | --- |
| 2026-09-14T23:06:40+0500 | OK |

## Notes

- Last scan run: 2026-09-14 23:06 local time with `run-scan.cmd backend` (coverage report generated first via `python -m pytest --cov=student_management --cov-report=xml:backend/coverage.xml`).
- Full suite: **205 tests pass**, `python -m ruff check .` clean.
- Live smoke: `backend/scripts/smoke_live.py` — **20/20 checks pass** (health, brand, admin/teacher/parent logins, students, CSV export, courses, attendance, portal children, PDF bytes, SPA fallback, API 404, PLUS create ops: POST /students, /enrollments, /attendance, /grades with readbacks), verified from the replicated Docker layout.
- Prod bootstrap: `scripts.create_admin.py` refuses the demo default, enforces ≥12 chars, idempotent; production startup runs only `alembic upgrade head` then `uvicorn` (never seeds).
- Raw API data: see `backend/sonar-data.json`.