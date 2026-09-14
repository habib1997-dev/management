# SonarQube Scan Report — management-frontend

- **Date:** 2026-09-14
- **Server:** SonarQube Community 26.9.0.129388 — `http://localhost:9000`
- **Project key:** `management-frontend`
- **Scanner:** sonar-scanner CLI (Java 21)
- **Profile:** Sonar way (built-in)

## Result Summary

| Metric | Before | After |
| --- | --- | --- |
| Code smells (open) | 58 | **0** |
| Lines of code (ncloc) | – | 3409 |
| Cognitive complexity | – | 265 |
| Duplicated lines density | – | 5.9% |

All 58 reported code smells were fixed and verified with a fresh analysis. The
dashboard shows **0 open issues** for the project.

## Issues Fixed by Rule

| Rule | Title | Fixed |
| --- | --- | --- |
| `javascript:S6772` | JSX elements spacing — insert explicit `{' '}` between text and adjacent inline element | 30 |
| `javascript:S3358` | Nested ternary operations — extract into independent if/else statements | 17 |
| `css:S7924` | Text contrast — use colors with sufficient contrast ratio | 3 |
| `javascript:S7786` | `new Error()` too unspecific — use `new TypeError()` | 2 |
| `javascript:S6582` | Prefer optional chaining over `&&` guard + property access | 1 |
| `javascript:S6481` | Context `value` changes every render — wrap in `useMemo` | 1 |
| `javascript:S7785` | Prefer top-level `await` over an async `boot()` call | 1 |
| `javascript:S7773` | Prefer `Number.parseInt` over `parseInt` | 1 |
| `javascript:S7744` | Empty object in object spread is useless | 1 |
| `javascript:S3776` | Cognitive complexity of `Parents` too high (22 > 15) | 1 |

## Files Changed

- `src/api.js` — (×2) `new Error()` → `new TypeError()`.
- `src/auth.jsx` — `login`/`logout` wrapped in `useCallback`; context `value`
  wrapped in `useMemo`.
- `src/brand.js` — `parseInt` → `Number.parseInt`.
- `src/main.jsx` — async `boot()` wrapper removed; top-level `await fetchBrand()`
  + render.
- `src/styles.css` — hover states switched to explicit solid colors with verified
  contrast (L-7665 sidebar hover, `.btn-ghost:hover`); `.pill-off` text darkened.
- `src/pages/Attendance.jsx` — roster rendering extracted; explicit `{' '}` spacing.
- `src/pages/Courses.jsx` — picker/roster rendering extracted to if/else helpers;
  module-scope `studentCheckbox`; explicit `{' '}` spacing.
- `src/pages/Grades.jsx` — empty object in spread removed; form/recorded body
  rendering split into independent if/else chains; explicit `{' '}` spacing.
- `src/pages/Login.jsx` — explicit `{' '}` spacing in labels.
- `src/pages/Parents.jsx` — `listBody`/`pickerContent`/submit-label/checkbox
  logic extracted to module-scope helpers (complexity 22 → 18 → <15); explicit
  `{' '}` spacing.
- `src/pages/Portal.jsx` — portal body rendered via explicit if/else instead of
  one large nested ternary.
- `src/pages/Students.jsx` — `res && res.student_id` → `res?.student_id`;
  `submitLabel` helper; rendering split into if/else; explicit `{' '}` spacing.
- `src/pages/Teachers.jsx` — `submitLabel` helper; rendering via if/else;
  explicit `{' '}` spacing.
- `vite.config.js` — `build.target: 'es2022'` (required for the top-level `await`
  fix in `main.jsx`).

## Verification

- `npm run build` — passes after all changes.
- Re-scan (`sonar-scanner` against `sonar-project.properties`) — clean pass.
- `api/issues/search?projectKeys=management-frontend&resolved=false` — **0 issues**.