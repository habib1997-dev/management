# Deployment — Render + Neon (PostgreSQL)

This document records the step-by-step process for deploying the Student
Management System to **Render** (Docker web service) with a **Neon** Postgres
database.  It also serves as a run sheet for reproducing the deployment in the
future.

---

## Prerequisites

- A GitHub repo with the code pushed (this repo).
- A [Neon](https://neon.tech) account with a Postgres project + database created.
- A [Render](https://render.com) account linked to the same GitHub account.

---

## Step 1 — Neon database

1. Create a project in Neon (if you haven't already).
2. Go to **Connection Details** and copy the **PostgreSQL connection string**
   with `?sslmode=require` at the end.  It looks like:
   ```
   postgresql://neondb_owner:xxxx@ep-xxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
3. Keep this string — you'll paste it into Render as `DATABASE_URL`.

---

## Step 2 — Render service

1. In Render dashboard → **New** → **Web Service**.
2. Connect your GitHub repo.
3. Settings:
   | Field | Value |
   |---|---|
   | **Name** | `student-management` (or your choice) |
   | **Region** | closest to your users |
   | **Runtime** | Docker |
   | **Dockerfile** | `Dockerfile` (root of repo) |
   | **Instance type** | Starter (free tier) works for demos |
4. Add the environment variables:
   | Key | Value |
   |---|---|
   | `APP_ENV` | `prod` |
   | `DATABASE_URL` | *(paste the Neon connection string from Step 1)* |
   | `SECRET_KEY` | *(click Generate — Render creates a random 64-char string)* |
   | `ALLOWED_HOSTS` | `<your-service-name>.onrender.com` |
   | `BUILD_DEMO` | `false` |
5. Click **Create Web Service**.

Render will automatically:
- Pull your repo.
- Build the Docker image (frontend + backend in one image).
- Run `alembic upgrade head` → `python -m scripts.seed` → `uvicorn` (via the CMD).

---

## Step 3 — Verify

1. Once the deploy finishes, open `https://<your-service>.onrender.com`.
2. You should see the login page.
3. Log in with the seeded admin credentials:
   ```
   Email:    admin@schoolsystem.com
   Password: changeme123
   ```
4. Run through the smoke test:
   - Create a student, teacher, course, parent.
   - Assign teacher to course, add students to roster.
   - Teacher: mark attendance, record grades.
   - Parent: log in with the parent login (created via admin → Parents → edit → account), open portal, check attendance + grades, download report card PDF.
   - Admin: download CSV exports from Students page.

---

## Step 4 — Custom branding (optional)

1. In Render → **Environment** → add `BRAND_DEMO=false` (already set above).
2. Upload a logo via the admin settings panel, or replace
   `backend/src/student_management/static/branding/logo.png` in the repo and
   redeploy.
3. Set `SCHOOL_NAME`, `SCHOOL_TAGLINE`, `BRAND_PRIMARY_COLOR`,
   `BRAND_SECONDARY_COLOR` in the environment or via the admin API if needed.

---

## How the Docker image works

```
Dockerfile (multi-stage)
├── Stage 1 (node:20-alpine)
│   ├── npm ci → install frontend deps
│   ├── npm run build → Vite produces frontend/dist/
│   └── dist/ is a static SPA (index.html + hashed assets)
└── Stage 2 (python:3.11-slim)
    ├── pip install ./backend → installs all runtime deps from pyproject.toml
    ├── COPY frontend/dist → /app/frontend/dist
    └── CMD: alembic upgrade head && seed && uvicorn
```

`serve_frontend()` in `main.py` automatically mounts `frontend/dist` if it
exists (production), or skips silently if not (local dev via `npm run dev`).

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| App crashes on deploy | Check Render logs — usually a missing env var (`DATABASE_URL` or `SECRET_KEY`). |
| 403 Forbidden on every page | `ALLOWED_HOSTS` must exactly match your Render hostname (`foo.onrender.com`). |
| `Invalid school branding` on startup | A missing or corrupt `logo.png`.  Re-deploy or replace the file. |
| Login fails with correct password | The `users` row was not seeded.  Re-run deploy (CMD runs seed automatically), or check DB is reachable from Neon dashboard. |
| PDF says "TBD" in name/logo | Branding env vars not set, or logo file missing.  Set `BRAND_DEMO=false` and confirm logo exists. |
