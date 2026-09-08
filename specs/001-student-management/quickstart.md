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
DATABASE_URL=postgresql://postgres@localhost:5432/student_management
SECRET_KEY=your-secret-key-change-this
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 4. Database Migrations

Run Alembic migrations to create the schema:

```bash
alembic upgrade head
```

### 5. Start the Development Server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
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

```
Authorization: Bearer <token>
```

Each role's token scope limits access (see RBAC below).

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

### Parent Portal (parent)

A parent views their linked child(ren)'s grades, attendance, and enrollment:

**Endpoint**: `GET /api/v1/parents/{parent_id}/portal`

**Response** (200 OK): grouped by child, includes attendance and grade records. Parents cannot view students they are not linked to (403).

### Report Card PDF (admin/teacher)

**Endpoint**: `GET /api/v1/reports/{student_id}`

Returns a **PDF** (`application/pdf`) report card summarizing the student's grades, attendance, and course enrollments.

## Role-Based Access Control (RBAC)

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

The first administrator account must be created via the setup script or database seeder. Example:

```
POST http://127.0.0.1:8000/api/v1/administrators
```

With body:

```json
{
  "name": "System Administrator",
  "email": "admin@schoolsystem.com",
  "role": "admin"
}
```

Teacher and parent accounts are created through the admin flows above — either by passing an optional `password` when creating the teacher/parent, or later via the `POST /api/v1/teachers/{teacher_id}/account` / `POST /api/v1/parents/{parent_id}/account` endpoints. Each account has its own login credentials, and login is role-scoped (admin/teacher/parent).

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

1. Customize the data model for your institution's specific needs
2. Extend API endpoints for additional workflows (term scheduling, transcript requests, etc.)
3. Implement frontend admin/teacher/parent interfaces
4. Set up role-based access control for all three roles (admin, teacher, parent)
5. Configure data retention and archival policies
6. Customize the report card PDF template for your institution's branding