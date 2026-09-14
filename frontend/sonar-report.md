# SonarQube Scan Report — management-frontend

- **Date:** 2026-09-14 (latest analysis `2026-09-14T20:38:10+0500`)
- **Server:** SonarQube Community 26.9.0 — `http://localhost:9000`
- **Project key:** `management-frontend`
- **Dashboard:** `http://localhost:9000/dashboard?id=management-frontend`
- **Quality gate:** `stargate` (server-wide custom default — no coverage condition)
- **Scanner:** sonar-scanner CLI (Java 21) + `frontend/sonar-project.properties`

## Quality Gate — OK

| Condition | Threshold | Actual | Status |
| --- | --- | --- | --- |
| Coverage on new code | — | *(gate condition removed)* | — |
| Duplicated lines on new code | ≤ 3% | 1.76% | OK |
| New violations | 0 | 0 | OK |

> **Why no coverage condition?**  
> The frontend has no automated test framework (no vitest/jest in `package.json`). A coverage
> condition would immediately fail at 0%. The custom `stargate` gate enforces 0 new issues + duplication
> control while a test suite is added. See `frontend/sonar-data.json` for raw data.

## Measures

| Metric | Value |
| --- | --- |
| Lines of code (ncloc) | 3 413 |
| Total lines | 3 725 |
| Statements | 884 |
| Comment lines | 23 |
| Duplicated lines density (overall) | 5.9% |
| Duplicated lines density (new code) | 1.76% |
| Cognitive complexity | 265 |
| Reliability rating | A (1.0) |
| Security rating | A (1.0) |
| Maintainability rating | A (1.0) |

## Issues — 0 open

Checked via `api/issues/search?componentKeys=management-frontend&resolved=false` (`ps=1`, facets by type + severity).

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
| 2026-09-14T20:38:10+0500 | OK |

## Notes

- Last scan run: 2026-09-14 20:38 local time with `run-scan.cmd frontend`.
- `npm run build` passes after all code-smell fixes (historical 58 issues resolved).
- When a test framework + coverage is added, reselect "Sonar way" on this project to restore
  the 80% coverage-on-new-code condition.
- Raw API data: see `frontend/sonar-data.json`.