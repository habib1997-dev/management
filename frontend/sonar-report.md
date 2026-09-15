# SonarQube Scan Report — management-frontend

- **Date:** 2026-09-15 (latest analysis `2026-09-15T13:11:12+0500`)
- **Server:** SonarQube Community 26.9.0 — `http://localhost:9000`
- **Project key:** `management-frontend`
- **Dashboard:** `http://localhost:9000/dashboard?id=management-frontend`
- **Quality gate:** `stargate` (server-wide custom default — now enforces **coverage on new code ≥ 60%**)
- **Scanner:** sonar-scanner CLI (Java 21) + `frontend/sonar-project.properties`

## Quality Gate — OK

| Condition | Threshold | Actual | Status |
| --- | --- | --- | --- |
| Coverage on new code | ≥ 60% | 82.2% | OK |
| Duplicated lines on new code | ≤ 3% | 0.36% | OK |
| New violations | 0 | 0 | OK |

> **Coverage restored:** Frontend test suite added (Vitest + Testing Library, 107 tests, 91.6%
> lines) and `coverage/lcov.info` wired via `sonar.javascript.lcov.reportPaths`. The `stargate`
> gate was updated (2026-09-15) to enforce `new_coverage >= 60%`. Baseline = Option B (60% bar),
> backend stays on "Sonar way" at 95.8%.

## Measures

| Metric | Value |
| --- | --- |
| Lines of code (ncloc) | 3 413 |
| Total lines | 3 725 |
| Statements | 884 |
| Comment lines | 23 |
| Coverage (overall) | 85.5% |
| Coverage on new code | 82.2% |
| Lines to cover | 985 |
| Uncovered lines | 79 |
| Duplicated lines density (overall) | 5.9% |
| Duplicated lines density (new code) | 0.36% |
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
| 2026-09-15T13:11:12+0500 | OK |
| 2026-09-15T13:00:42+0500 | OK |
| 2026-09-14T07:35:02+0500 | OK |

## Notes

- Last scan run: 2026-09-15 13:11 local time (frontend coverage session).
- Test suite: 107 Vitest tests across 14 files (`src/__tests__/`); run locally with
  `npm.cmd run test` / `npm.cmd run test:coverage`. Coverage 91.6% lines locally (Sonar's
  combined lines+conditions metric reads 85.5%).
- 16 S9020 "un-awaited expectation" MINOR smells (from the 13:00 analysis) fixed by switching
  post-action assertions to `expect(await screen.findBy*())`; re-scan at 13:11 shows 0 issues.
- SCM "missing blame information" warnings appear only while `src/__tests__/` files are
  untracked (pre-first-commit); they resolve once committed.
- `npm run build` passes (dist rebuilt after all code-smell fixes).
- Raw API data: see `frontend/sonar-data.json`.