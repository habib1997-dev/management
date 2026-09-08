# Research.md: Student Management System

**Generated**: 2026-09-06  
**Feature**: 001-student-management  
**Purpose**: Resolve all NEEDS CLARIFICATION items from Technical Context before Phase 1 design

## Research Items

### 1. Language/Version

- **Decision**: Python 3.11 + FastAPI selected
- **Rationale**: FastAPI provides modern Python type hints, automatic API documentation, and built-in validation - well-suited for a student management system with data validation requirements. Python's readability reduces onboarding time for educational institutions.
- **Alternatives considered**:
  - Node.js/Express: Strong JavaScript ecosystem, but type safety requires Flow or TypeScript learning curve
  - Java Spring Boot: Enterprise-grade, but heavier setup and longer development cycle for this scope
  - Ruby on Rails: Rapid development, but performance concerns for 1000+ concurrent users

### 2. Primary Dependencies

- **Decision**: SQLAlchemy ORM + Pydantic validation + JWT-auth
- **Rationale**: SQLAlchemy provides flexible database mapping with SQLite for development and PostgreSQL for production. Pydantic enables data validation through Python type definitions. JWT-auth provides standard token-based authentication for administrator access.
- **Alternatives considered**:
  - Django ORM: Batteries-included but less flexible for custom queries
  - TypeScript + TypeORM: Type safety benefits but adds build complexity
  - Hibernate (Java): Powerful but significant overhead for this feature scope

### 3. Storage (Database)

- **Decision**: PostgreSQL 15 as primary database
- **Rationale**: Open-source relational database with excellent JSONB support for flexible student data, strong integrity constraints, and proven reliability at scale. FERPA-compatible data retention possible with proper configuration.
- **Alternatives considered**:
  - MySQL: Similar capabilities but PostgreSQL has superior JSON support and newer feature set
  - SQLite: Good for development/local use but not suitable for multi-administrator concurrent access
  - MongoDB: Document-oriented but loses relational integrity benefits for student-parent-course relationships

### 4. Testing Strategy

- **Decision**: pytest with fixtures + coverage reporting + integration test suite
- **Rationale**: pytest is mature Python testing framework with fixture support for database test isolation. Coverage reporting ensures minimum test coverage. Separate unit, integration, and end-to-end test layers validate all student management workflows.
- **Alternatives considered**:
  - unittest: Built-in but more verbose than pytest
  - Jest: JavaScript testing, would require language switch
  - PyTest + Django test client: Too tightly coupled to Django for this flexible setup

### 5. Target Platform

- **Decision**: Web application (browser-based admin interface)
- **Rationale**: Accessible from any device, no installation required for administrators, easy to update. Responsive design works on desktops and tablets used by school staff.
- **Alternatives considered**:
  - Desktop application (Electron/WPF): Requires installation, harder to update across institution
  - Mobile app (iOS/Android): Overkill for administrator workflows; limited screen real estate for data entry
  - Hybrid approach: Adds complexity without significant benefit for core use cases

### 6. Performance Goals

- **Decision**: Support 1000 concurrent student records; enrollment API response under 3 seconds; page load under 2 seconds
- **Rationale**: Based on industry standards for educational administration systems. 1000 concurrent records handles typical medium-sized school enrollment. Response time targets ensure administrators can work efficiently without perceivable delays.
- **Alternatives considered**:
  - 500 concurrent records: Too restrictive for growing institutions
  - 5000 concurrent records: Over-engineering for initial release; higher infrastructure costs
  - No specific targets: Would risk poor user experience and difficulty measuring success

### 7. Constraints & Compliance

- **Decision**: FERPA compliance for student data privacy; 7-year data retention minimum; role-based access control (RBAC) for administrator permissions
- **Rationale**: FERPA (Family Educational Rights and Privacy Act) governs student education record privacy in the US. 7-year retention aligns with common educational record keeping practices. RBAC ensures only authorized staff can perform specific operations (e.g., teachers can view their students, admins can manage all students).
- **Alternatives considered**:
  - No formal compliance: Risky for educational institution data; potential legal issues
  - GDPR compliance: Required if data includes EU students/parents, adds complexity beyond FERPA
  - No RBAC: Security risk; every user would have all permissions

### 8. Scale & Scope

- **Decision**: Support 500-2000 students per institution; up to 50 concurrent administrators; single-institution deployment for v1
- **Rationale**: Covers range from small private schools to medium public school districts. Single-institution v1 scope keeps initial complexity manageable while delivering immediate value. Multi-institution support can be v2 enhancement.
- **Alternatives considered**:
  - 100 students only: Too limiting; doesn't serve most educational institutions
  - Unlimited students: Impossible to test; over-scoped for v1; higher infrastructure costs
  - Multi-institution v1: Distributes focus; increases complexity; defers core value delivery

## Supplemental Research (Expanded Features: 2026-09-07)

The following research items were added when the spec expanded to include attendance, grades, courses, parents/parent portal, reports, and three-role RBAC.

### 9. Role-Based Access Control (RBAC)

- **Decision**: Three roles — **admin**, **teacher**, **parent** — enforced via JWT claims and per-request dependency checks in FastAPI.
- **Rationale**: FastAPI dependency-injection makes role guards declarative (e.g., `Depends(require_role("admin"))`). Roles are simple and unambiguous for a single-institution v1. Admin inherits all teacher capabilities.
- **Alternatives considered**:
  - Fine-grained permission/ACL model (e.g., Casbin, Oso): More flexible but over-engineered for 3 roles in v1
  - Single admin role only: Cannot satisfy the confirmed requirements (teachers have login, parents have portal)
  - Attribute-based access control: Adds complexity not justified for this scope

### 10. PDF Report Card Generation

- **Decision**: **ReportLab** (`reportlab`) for server-side PDF report card export, served as `application/pdf` from `GET /api/v1/reports/{student_id}`.
- **Rationale**: ReportLab is the de-facto standard for programmatic PDF generation in Python, mature, pure-Python (no OS dependencies), and allows fine-grained layout control for report cards (tables of grades, attendance summary). It integrates cleanly with FastAPI by returning a `Response` with `media_type="application/pdf"`.
- **Alternatives considered**:
  - WeasyPrint (HTML/CSS to PDF): Easier templating but heavy dependencies (GTK/WebKit) and noisier to deploy
  - wkhtmltopdf: External binary dependency, harder to install on all hosts
  - LaTeX (via pdflatex): Overkill and slow for dynamic per-student generation
  - Client-side print-to-PDF: No server-side canonical artifact; unreliable layout

### 11. Parent Portal Read-Only Access

- **Decision**: A read-only portal endpoint (`GET /api/v1/parents/{parent_id}/portal`) that returns the parent's linked children with their grades, attendance, and enrollment. Parent identity/role from JWT; the endpoint verifies ownership so a parent cannot view children they are not linked to (403).
- **Rationale**: Read-only aligns with FERPA (parents access their own child's records) and keeps the portal simple and secure. JWT role enforcement prevents cross-child access.
- **Alternatives considered**:
  - Full parent CRUD in portal: Unnecessary; parents only need read access
  - Self-service parent registration: Delays v1; admin-managed parent records are simpler and safer

### 12. Attendance & Grading Rules

- **Decision**: Attendance is marked daily **per course** (`POST /api/v1/attendance` with a `records` array of student/status pairs; statuses present/absent/late/excused). Teachers may only mark attendance for courses they are assigned to. Grades are 0-100 decimals recorded per student per course with assignment metadata (quiz/test/homework/final).
- **Rationale**: Daily-per-course matches the confirmed "daily attendance per class period" requirement. Constraining teachers to their own courses (checked against `Teacher.course` assignments) enforces RBAC at the data level.
- **Alternatives considered**:
  - Whole-day attendance (single record per student/day): Simpler but does not meet per-class-period requirement
  - Letter-grade-only system: Confirmed 0-100 numeric scale; storing numeric allows computed averages for report cards
  - Free-text grade entry: Loses validation and the 0-100 invariant (FR-014)

### 13. Course/Class Management & Parent Linking

- **Decision**: Courses have a name, assigned teacher (one teacher per course for v1), grade level, semester, max students, and status. Parents are linked to one or more students via a join relation.
- **Rationale**: One-teacher-per-course keeps the model simple while covering the common case. Parent↔student is many-to-many (a parent can have multiple children, a student can have multiple guardians).
- **Alternatives considered**:
  - Co-teaching (multiple teachers per course): Adds join-table complexity not needed for v1
  - Parent linked to single student only: Fails common multiple-children households

### 14. Frontend Framework (RESOLVED 2026-09-07)

- **Decision**: **React** (with Vite for scaffolding).
- **Rationale**: Industry standard with the largest ecosystem and best AI-tool support; matches the components/pages/services structure already in plan.md. The administrator/teacher/parent interfaces are a straightforward CRUD + forms app, well-covered by React patterns.
- **Alternatives considered**:
  - Jinja2/HTMX (server-rendered): Simpler but less maintainable for interactive portals
  - Vue: Slightly easier to learn but smaller ecosystem and fewer AI examples
  - Skip frontend for v1: Rejected - users confirmed they want browser screens

### 15. Login / Account Model (RESOLVED 2026-09-07)

- **Decision**: **One `users` table** holding all accounts: `email`, `password_hash`, `role` (`admin`/`teacher`/`parent`), plus optional FK links to the Teacher/Parent records. Passwords hashed with bcrypt; JWT bearer tokens issued at login.
- **Rationale**: Single source of truth for authentication; standard pattern; simplest for the 3-role model. Aligns with the existing "emails unique across system" constraint.
- **Alternatives considered**:
  - Separate account tables per role: Duplicated login logic and sync issues, no benefit

### 16. Delivery Approach (RESOLVED 2026-09-07)

- **Decision**: **MVP-first**. Build Phases A + B + student core (US1), then stop for user validation before building the remaining features/phases.
- **Rationale**: The MVP shares its foundation (database, login, services) with all later phases - nothing is thrown away. Early user validation avoids building 5 features on a misunderstanding.

## Summary of Resolved Clarifications

All 8 NEEDS CLARIFICATION items from the Technical Context have been researched and decisions documented above, plus 8 supplemental research items (9-16) covering the expanded features and the resolved v1 decisions (React, one users table, MVP-first). No unresolved clarifications remain. Research findings support proceeding to Phase 1 (data-model design and API contract generation).

**Next Phase**: Phase 1 - Generate data-model.md, API contracts (contracts/), and quickstart.md