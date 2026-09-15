# Quickstart: Student Management System

**Generated**: 2026-09-07  
**Feature**: 001-student-management  
**Purpose**: Get the student management system running with minimal setup

The system supports three roles — **admin**, **teacher**, and **parent**:
- **Admin**: full access — students, teachers, courses, parents, reports
- **Teacher**: mark attendance + record grades for their own courses
- **Parent**: view-only access to their linked child(ren)'s progress via the portal

All roles log in through a **single user accounts system** (email + password); the account's role decides what you can see and do. The browser interface is a **React** app served from `frontend/`.

## Prerequisites

- Python 3.11 or newer
- PostgreSQL 15+ with database `student_management` created
- `pip install fastapi uvicorn sqlalchemy pydantic pytest httpx reportlab`

## Setup

### 1. Database Configuration

Create the PostgreSQL database:

```bash
createdb student_management
```

Alternatively, update the database connection string in `app/config.py`.

### 2. Application Installation

Install the package in development mode:

```bash
pip install -e .
```

### 3. Environment Variables

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```
APP_ENV=dev
DATABASE_URL=postgresql://postgres@localhost:5432/student_management
SECRET_KEY=dev-secret-key-change-me-32bytes-minimum
ALLOWED_HOSTS=localhost,127.0.0.1
```

Environment meanings (enforced at startup — an invalid value refuses to run):
- `dev` — development only (lenient: auto-creates tables).
- `prod` or `production` — production: requires PostgreSQL
  (`postgresql://` or `postgresql+psycopg://`), an explicit `ALLOWED_HOSTS`,
  and an explicit `SECRET_KEY` (≠ the dev default, ≥ 32 characters).
- Anything else (e.g. `staging`) → startup error.

School branding also lives here (single source — the login page, sidebar, tab
title and report-card PDF all read it):

```
SCHOOL_NAME=Usman Public School
SCHOOL_TAGLINE=Knowledge, Character, Excellence
BRAND_PRIMARY_COLOR=#0B6B4F
BRAND_SECONDARY_COLOR=#D9A441
BRAND_DEMO=true
SCHOOL_LOGO=logo.png
```

To rebrand for a real school, just change these values (and drop a logo file
named to match `SCHOOL_LOGO` into the branding folder).

### 4. Database Migrations

Run Alembic migrations to create the schema:

```bash
alembic upgrade head
```

### 5. Start the Development Server

```bash
uvicorn student_management.main:app --reload --host 127.0.0.1 --port 8000
```

The server will start at `http://127.0.0.1:8000`.

## API Endpoints

### Enroll a New Student

**Endpoint**: `POST http://127.0.0.1:8000/api/v1/students`

**Request** (JSON):

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "2015-05-15",
  "grade_level": "9",
  "email": "john.doe@schoolsystem.com",
  "phone": "555-123-4567"
}
```

> **Note:** `grade_level` is free text (up to 20 characters). Schools may use their own labels such as `"K"`, `"Grade 5"`, `"K-1"`, or `"O-Level"` — the system no longer restricts grades to K-12.

**Response** (201 Created):

```json
{
  "success": true,
  "student": {
    "student_id": "123e4567-e89b-12d3-a456-426614174000",
    "first_name": "John",
    "last_name": "Doe",
    "grade_level": "9",
    "active": true,
    "enrollment_date": "2026-09-06",
    "date_of_birth": "2015-05-15",
    "email": "john.doe@schoolsystem.com",
    "phone": "555-123-4567"
  },
  "message": "Student successfully enrolled"
}
```

### View Student List

**Endpoint**: `GET http://127.0.0.1:8000/api/v1/students`

**Query Parameters** (optional):

- `page`: 1 (default)
- `pageSize`: 20 (default)
- `gradeLevel`: filter by grade
- `active`: true/false

**Response** (200 OK):

```json
{
  "data": [
    {
      "student_id": "123e4567-e89b-12d3-a456-426614174000",
      "first_name": "John",
      "last_name": "Doe",
      "grade_level": "9",
      "active": true,
      "enrollment_date": "2026-09-06"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 1
  }
}
```

### Update Student Information

**Endpoint**: `PUT http://127.0.0.1:8000/api/v1/students/{student_id}`

**Request** (JSON - only fields to update):

```json
{
  "phone": "555-987-6543"
}
```

**Response** (200 OK):

```json
{
  "success": true,
  "student": {
    "student_id": "123e4567-e89b-12d3-a456-426614174000",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "555-987-6543"
  },
  "message": "Student successfully updated"
}
```

### Authentication

All requests except the login endpoint require a bearer token. Obtain one by providing credentials:

```
POST http://127.0.0.1:8000/api/v1/auth/login
```

```json
{ "email": "admin@your-school.org", "password": "your-password-here" }
```

```json
{
  "access_token": "<jwt>",
  "role": "teacher",
  "user_id": "123e4567-e89b-12d3-a456-426614174001",
  "email": "jane.smith@schoolsystem.com",
  "teacher_id": "123e4567-e89b-12d3-a456-426614174002"
}
```

The login response carries `teacher_id` for teachers and `parent_id` for parents (the admin/teacher/parent profile id you need for role-scoped endpoints).

```
Authorization: Bearer <token>
```

Each role's token scope limits access (see RBAC below). Login is throttled: 5 failed attempts per email + client IP within 15 minutes returns `429 Too Many Requests`; a successful login resets the counter.

### Search Students

The student list endpoint supports a `search` query parameter (FR-003) that matches first or last name:

```
GET /api/v1/students?search=doe&gradeLevel=9
```

### Teachers

**Create a teacher** (admin-only):

**Endpoint**: `POST /api/v1/teachers`

```json
{
  "name": "Jane Smith",
  "email": "jane.smith@schoolsystem.com",
  "subjects_taught": "Mathematics",
  "password": "teacherpw123"
}
```

The `password` field is **optional**. If provided, a login account is created for the teacher right away. If omitted, you can add one later:

**Endpoint**: `POST /api/v1/teachers/{teacher_id}/account`

```json
{
  "password": "teacherpw123"
}
```

**List teachers**: `GET /api/v1/teachers`
**Get a teacher**: `GET /api/v1/teachers/{teacher_id}`

### Courses

**Create a course** (admin-only):

**Endpoint**: `POST /api/v1/courses`

```json
{
  "name": "Algebra I",
  "teacher_id": "123e4567-e89b-12d3-a456-426614174001",
  "grade_level": "9",
  "semester": "Fall 2026",
  "max_students": 30
}
```

**List courses**: `GET /api/v1/courses?teacherId=<uuid>&gradeLevel=9`
**Get a course**: `GET /api/v1/courses/{course_id}`
**Update a course**: `PUT /api/v1/courses/{course_id}`
**List students in a course**: `GET /api/v1/courses/{course_id}/students`
**Assign students to a course** (admin-only): `PUT /api/v1/courses/{course_id}/students`

```json
{
  "student_ids": ["123e4567-e89b-12d3-a456-426614174003", "123e4567-e89b-12d3-a456-426614174004"]
}
```

### Mark Daily Attendance (teacher)

**Endpoint**: `POST /api/v1/attendance`

**Request** (JSON):

```json
{
  "course_id": "123e4567-e89b-12d3-a456-426614174002",
  "date": "2026-09-07",
  "records": [
    { "student_id": "123e4567-e89b-12d3-a456-426614174000", "status": "present" },
    { "student_id": "123e4567-e89b-12d3-a456-426614174003", "status": "absent" }
  ]
}
```

**Response** (201 Created): returns the attendance records created.

**Get course attendance**: `GET /api/v1/attendance/{course_id}?date=2026-09-07`
**Get a student's attendance**: `GET /api/v1/students/{student_id}/attendance`

### Record Grades (teacher)

**Endpoint**: `POST /api/v1/grades`

**Request** (JSON):

```json
{
  "student_id": "123e4567-e89b-12d3-a456-426614174000",
  "course_id": "123e4567-e89b-12d3-a456-426614174002",
  "grade_value": 92.5,
  "assignment_type": "test",
  "date_assigned": "2026-09-01",
  "date_due": "2026-09-05"
}
```

Grade values must be between 0 and 100. **Get a student's grades**: `GET /api/v1/students/{student_id}/grades?courseId=<uuid>`
**Get course grades**: `GET /api/v1/courses/{course_id}/grades`

A teacher can only see/record grades for students in **their own courses** (course assignments are checked server-side); a filtered lookup on another teacher's course returns **403**. Admins can record and view grades in any course.

**Edit an existing grade** (teacher of the course, or admin): `PUT /api/v1/grades/{grade_id}`

```json
{ "grade_value": 95.0 }
```

`grade_value` (0–100), `assignment_type` (quiz/test/homework/final), `date_assigned`, and `date_due` are all optional — only provided fields change, and the student + course cannot be changed. Editing a grade updates the same row (never duplicates it).

### Manage Parents (admin)

**Create a parent** (admin-only):

**Endpoint**: `POST /api/v1/parents`

```json
{
  "name": "Maria Doe",
  "email": "maria.doe@family.net",
  "phone": "555-222-3333",
  "student_ids": ["123e4567-e89b-12d3-a456-426614174000"],
  "password": "parentpw123"
}
```

The `password` field is **optional**. If provided, a login account is created for the parent right away. If omitted, you can add one later:

**Endpoint**: `POST /api/v1/parents/{parent_id}/account`

```json
{
  "password": "parentpw123"
}
```

**List parents**: `GET /api/v1/parents`
**List a parent's students**: `GET /api/v1/parents/{parent_id}/students`
**List a student's parents**: `GET /api/v1/students/{student_id}/parents` — admins for any student; teachers only for students they teach (so they can call a guardian about absence or poor performance); parents get `403`.
**List parents for a whole course** (teachers, own courses only): `GET /api/v1/courses/{course_id}/parents` — returns one row per enrolled student with that student's parent list (name, email, phone). This is what the teacher Attendance and Grades screens use for the "Parent contact" column.
**Change a parent's children later** (admin-only): `PUT /api/v1/parents/{parent_id}/students` with `{"student_ids": [...]}` — replaces the linked children (e.g. a second child joins the school).

### Privacy rules

- **Student email and phone are admin-only.** Teacher-facing student lists/details return them as `null`; the parent portal and PDF reports never include student contact info.
- **Parent name/email/phone are visible to admins and to teachers of that student's courses** (for guardian outreach), never to other parents.

### Account management (admin)

Admins can see all login accounts, disable a login (e.g. a teacher who left the school), or reset a forgotten password:

**List accounts**: `GET /api/v1/administrators/users`

**Update an account**: `PUT /api/v1/administrators/users/{user_id}`

```json
{ "active": false }            // disable this login
{ "active": true }             // re-enable it
{ "password": "newpass123" }   // reset the password
```

Note: courses enforce their `max_students` size on roster assignment — assigning more students than the limit returns a "Course capacity exceeded" error.

### Remove someone (deactivate / restore)

No data is ever permanently erased — records are **soft-deleted** so history (courses, grades, attendance) stays intact. Set the record's flag to `false` to deactivate; it also disables the person's login. Set it back to `true` to restore.

In the website, each screen has an **Edit** button whose panel lets an admin fix mistakes **and** toggle "Account active" in one place (un-tick to deactivate). Behind the scenes:
**Edit a teacher** (admin-only): `PUT /api/v1/teachers/{teacher_id}` — optional `name`, `email`, `subjects_taught`, `status`, and `password` (resets their login, or creates a first login if they never had one)

**Edit a parent** (admin-only): `PUT /api/v1/parents/{parent_id}` — optional `name`, `email`, `phone`, `status`, and `password` (same behavior as teachers; use `PUT /parents/{id}/students` separately to change linked children)
**Edit/deactivate a student** (admin-only): `PUT /api/v1/students/{student_id}` — optional `name`, `email`, `phone`, `active`, `date_of_birth`, `grade_level`

Only provided fields change. A second parent/teacher with the same email is rejected (400), and email/phone are format-checked.

What being deactivated means:
- Teacher: can't be assigned to new courses ("Cannot assign an inactive teacher"), login disabled.
- Parent: portal access refused ("Parent account is deactivated"), login disabled.
- Student: can't receive new attendance marks or grades ("Student is deactivated").

### Parent Portal (parent)

A parent views their linked child(ren)'s grades, attendance, and enrollment:

**Endpoint**: `GET /api/v1/parents/{parent_id}/portal`

**Response** (200 OK): grouped by child, includes attendance and grade records. Parents cannot view students they are not linked to (403). The `parent_id` comes from the **login response** (`POST /api/v1/auth/login` returns `parent_id` for parents and `teacher_id` for teachers).

### Report Card PDF (admin/teacher)

**Endpoint**: `GET /api/v1/reports/{student_id}`

Returns a **PDF** report summarizing the student's grades, attendance, and course enrollments.
- **Admin**: gets the full **Academic Report Card** for any student (filename `report_card_…`).
- **Teacher**: gets an **Academic Progress Report** scoped to their own courses only (filename `progress_report_…`); a teacher who does not teach the student gets **403**.

### Report Card PDF (parent — own children)

**Endpoint**: `GET /api/v1/reports/portal/{student_id}`

Lets a parent download the full report card PDF for one of their **own linked children** only; otherwise **403**.

## School branding (single source)

Branding is stored in one place — `backend/src/student_management/config.py` + the branding folder — and is read by both the public API and the PDF builder (never fetched over HTTP):

- **Settings API (public-ish)**: `GET /api/v1/settings/brand` → school name, tagline, colors, `demo` flag, logo URL. The logo itself: `GET /api/v1/settings/brand/logo` (served as an image; also used as the browser tab favicon).
- **Files**: the logo lives in `backend/src/student_management/static/branding/`. The config value `SCHOOL_LOGO` is a plain filename (path separators/reversal rejected, only `.png/.jpg/.jpeg/.webp` allowed); a missing file stops the server at startup rather than failing at runtime.
- **Demo crest**: `python -m scripts.make_logo` (from `backend/`) regenerates the original green/gold crest `logo.png` (needs Pillow). The demo flag makes the login page show a "Demo preview" badge.
- The PDF report card's letterhead (logo + name + tagline + gold accent bar) comes from this same service, so rebranding for a sale is a one-time config + logo change.

## Backup & restore

**Create a backup** (from `backend/`):

```bash
python -m scripts.backup
```

Writes a timestamped snapshot into `backend/backups/` (e.g. `student_management_20260909-154325.db`). SQLite uses the online backup API (safe while the server is running); PostgreSQL uses `pg_dump`. `backups/` is git-ignored — for a real deployment, store backups encrypted off-server.

**List backups**:

```bash
python -m scripts.backup --list
```

**Restore a backup** — always requires the explicit `--confirm` flag; a snapshot of the current state (`pre_restore_…`) is saved automatically first:

```bash
python -m scripts.backup --restore --file student_management_20260909-154325.db --confirm
```

For PostgreSQL, backups are `.sql`/`.dump` files restored with `pg_restore`.

## CSV data exports (admin)

Export student and grade data as spreadsheet files (no login pages needed — csv formula-injection is defused so cells starting with `= + - @` can't run as formulas):

- `GET /api/v1/export/students.csv`
- `GET /api/v1/export/grades.csv`

Both require an **admin** bearer token. In the website, the Students page has "Download students CSV" / "Download grades CSV" buttons.

## RBAC quick reference

| Operation | Admin | Teacher | Parent |
|-----------|:-----:|:-------:|:------:|
| Student CRUD | ✅ | ❌ | ❌ |
| Teacher CRUD | ✅ | ❌ | ❌ |
| Course CRUD | ✅ | ❌ | ❌ |
| Mark attendance (own courses) | ✅ | ✅ | ❌ |
| Record grades (own courses) | ✅ | ✅ | ❌ |
| Parent records | ✅ | ❌ | ❌ |
| Parent portal (own children only) | ❌ | ❌ | ✅ |
| Report card PDF | ✅ | ✅ (own courses) | ❌ |

## Testing

Run the test suite:

```bash
pytest
```

All tests should pass. Test files are located in `tests/` directory.

## Default Admin Account

One admin login is created by the database seeder (from `backend/`):

```bash
python -m scripts.seed
```

That creates the admin account `admin@schoolsystem.com`. The admin password is **not** committed anywhere — it comes from the `ADMIN_PASSWORD` environment variable (or an interactive prompt with `--interactive`), and the demo teacher/parent logins use `DEMO_TEACHER_PASSWORD` / `DEMO_PARENT_PASSWORD`. This is dev only — in **production** the seeder never runs; the first admin is created once via `python -m scripts.create_admin` with a private password, see `deployment.md` Step 3. Teacher and parent accounts are created through the admin flows above — either by passing an optional `password` when creating the teacher/parent, or later via the `POST /api/v1/teachers/{teacher_id}/account` / `POST /api/v1/parents/{parent_id}/account` endpoints. Each account has its own login credentials, and login is role-scoped (admin/teacher/parent).

## Directory Structure

```
specs/001-student-management/
├── plan.md              # Implementation plan
├── research.md          # Research findings
├── data-model.md        # Entity definitions
├── contracts/
│   └── openapi.yaml     # API specification
├── quickstart.md        # This file
└── spec.md              # Feature specification
```

## Next Steps

1. Rebrand for the client school: change the `SCHOOL_*`/`BRAND_*` values in `.env`, swap the logo file, set `BRAND_DEMO=false`.
2. Deploy to production: PostgreSQL + Alembic migrations + `SECRET_KEY`/`ALLOWED_HOSTS`/`APP_ENV=prod`, HTTPS, and encrypted off-server backups (see "Backup & restore").
3. Extend API endpoints for additional workflows (term scheduling, transcript requests, etc.)