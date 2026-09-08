# Data Model: Student Management System

**Generated**: 2026-09-07  
**Feature**: 001-student-management  
**Based on**: specs/001-student-management/spec.md

## Entities

### Student

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `student_id` | UUID | System-generated unique identifier | Required, auto-generated |
| `first_name` | String (100) | Student's first name | Required, min 1 char, max 100 |
| `last_name` | String (100) | Student's last name | Required, min 1 char, max 100 |
| `date_of_birth` | Date | Student's date of birth | Required, must be past date, age 5-18 typical |
| `grade_level` | String (20) | Current grade level | Required, min 1 char, max 20. Free text so schools can use their own labels (e.g. `"K"`, `"9"`, `"K-1"`, `"O-Level"`) |
| `enrollment_date` | Date | Date student was enrolled | Required, must be <= today, <= date_of_birth + 5 years |
| `email` | String (200) | Student email address (if applicable) | Optional, must be valid email format if provided |
| `phone` | String (50) | Student phone number (if applicable) | Optional, must match phone format if provided |
| `active` | Boolean | Whether student record is active | Default: true |

**Relationships**:
- One student has one primary enrollment record
- Student may have multiple contact records (parents/guardians)
- Student may be associated with course enrollments (in academic term models)
- Student has many attendance records
- Student has many grade records
- Student is linked to one or more parents/guardians

### Enrollment

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `enrollment_id` | UUID | System-generated unique identifier | Required, auto-generated |
| `student_id` | UUID | Foreign key to Student | Required, exists in Student table |
| `enrolled_by` | String (100) | Administrator who enrolled the student | Required |
| `enrollment_date` | Date | Date of enrollment | Required, must be <= today |
| `status` | String (20) | Enrollment status | Required, enum: ['active', 'withdrawn', 'transferring'] |

**Relationships**:
- One enrollment belongs to one student
- One student may have multiple enrollment records (historical)

### Teacher

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `teacher_id` | UUID | System-generated unique identifier | Required, auto-generated |
| `name` | String (100) | Teacher's full name | Required, min 1 char, max 100 |
| `email` | String (200) | Teacher email address | Required, valid email format |
| `subjects_taught` | String (100) | Subjects or courses teacher instructs | Optional, comma-separated list |
| `status` | Boolean | Whether teacher account is active | Default: true |

**Relationships**:
- One teacher may teach many courses
- One course is assigned to one teacher
- One teacher may have many attendance records (for their classes)
- One teacher may have many grade records (for their students)

### Course

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `course_id` | UUID | System-generated unique identifier | Required, auto-generated |
| `name` | String (100) | Course name (e.g., "Math 101", "Grade 5 Science") | Required, min 1 char, max 100 |
| `teacher_id` | UUID | Foreign key to Teacher | Required, exists in Teacher table |
| `grade_level` | String (20) | Target grade level for this course | Required, min 1 char, max 20. Free text so schools can use their own labels (e.g. `"K"`, `"9"`, `"K-1"`, `"O-Level"`) |
| `semester` | String (20) | Academic semester (e.g., "Fall 2024", "Spring 2025") | Required |
| `max_students` | Integer | Maximum number of students allowed | Optional, default: 30 |
| `status` | String (20) | Course status | Required, enum: ['active', 'inactive', 'full'] |

**Relationships**:
- One course is assigned to one teacher
- One course has many enrolled students
- One student may be enrolled in many courses

### Parent

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `parent_id` | UUID | System-generated unique identifier | Required, auto-generated |
| `name` | String (100) | Parent/guardian full name | Required, min 1 char, max 100 |
| `email` | String (200) | Parent email address | Required, valid email format |
| `phone` | String (50) | Parent phone number | Required, must match phone format |
| `status` | Boolean | Whether parent account is active | Default: true |

**Relationships**:
- One parent may be linked to many students
- One student may have one or more parents linked
- Parent has view-only access to linked student's portal

### Attendance

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `attendance_id` | UUID | System-generated unique identifier | Required, auto-generated |
| `student_id` | UUID | Foreign key to Student | Required, exists in Student table |
| `course_id` | UUID | Foreign key to Course | Required, exists in Course table |
| `date` | Date | Attendance date | Required, must be a valid school day |
| `status` | String (10) | Attendance status | Required, enum: ['present', 'absent', 'late', 'excused'] |
| `marked_by` | UUID | Foreign key to Teacher who marked attendance | Required, exists in Teacher table |

**Relationships**:
- One attendance record belongs to one student
- One attendance record belongs to one course
- One student may have many attendance records (across courses and dates)
- One course may have many attendance records (across students and dates)
- One attendance record is marked by one teacher

### Grade

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `grade_id` | UUID | System-generated unique identifier | Required, auto-generated |
| `student_id` | UUID | Foreign key to Student | Required, exists in Student table |
| `course_id` | UUID | Foreign key to Course | Required, exists in Course table |
| `grade_value` | Decimal (5,2) | Numeric grade (e.g., 89.5, 95.0) | Required, min 0, max 100 |
| `assignment_type` | String (30) | Type of assessment (e.g., "quiz", "test", "homework", "final") | Optional |
| `date_assigned` | Date | When the assignment was given | Required |
| `date_due` | Date | When the assignment is due | Required, must be >= date_assigned |
| `date_graded` | Date | When the grade was recorded | Required, must be >= date_due |

**Relationships**:
- One grade record belongs to one student
- One grade record belongs to one course
- One student may have many grade records (across courses)
- One course may have many grade records (across students)

## Validation Rules Summary

### Required Fields (across all entities)
- Student: first_name, last_name, date_of_birth, grade_level, enrollment_date
- Enrollment: student_id, enrolled_by, enrollment_date
- Teacher: name, email
- Course: name, teacher_id, grade_level, semester
- Parent: name, email, phone
- Attendance: student_id, course_id, date, status
- Grade: student_id, course_id, grade_value, date_assigned, date_due, date_graded

### Cross-Entity Validation
- Student date_of_birth must be before enrollment_date
- Student grade_level must be age-appropriate for date_of_birth
- Enrollment enrollment_date must be on or after student's enrollment_date
- Administrator/Teacher email must be unique across system
- Student email (if provided) must be unique across students
- Parent email must be unique across parents
- Course teacher_id must exist in Teacher table
- Attendance student_id must exist in Student table
- Attendance course_id must exist in Course table
- Attendance marked_by must exist in Teacher table
- Grade student_id must exist in Student table
- Grade course_id must exist in Course table
- Grade grade_value must be between 0 and 100
- Grade date_due must be >= date_assigned
- Grade date_graded must be >= date_due

## State Transitions

### Student Record States
- **active**: Default state; student is currently enrolled
- **inactive**: Student has withdrawn or transferred; record preserved for history
- **archived**: Record older than retention policy; moved to cold storage

### Enrollment Status Transitions
- **active** → **withdrawn**: When student leaves the institution
- **active** → **transferring**: When student moves to another institution (with record transfer)
- **withdrawn** → **archived**: After retention period (7 years minimum)

### Teacher Account States
- **active**: Can perform teaching functions
- **suspended**: Temporarily restricted (e.g., pending investigation)
- **disabled**: Permanently deactivated (e.g., staff departure)

### Course States
- **active**: Course is currently running, students can enroll
- **inactive**: Course is not currently running
- **full**: Course has reached maximum student capacity

### Attendance Status States
- **present**: Student was present for the class
- **absent**: Student was absent for the class
- **late**: Student arrived after class started
- **excused**: Student was excused from attendance (e.g., illness, family emergency)

### Grade Status States
- **recorded**: Grade has been entered and saved
- **posted**: Grade has been posted to student/parent portal
- **final**: Grade is final for the term/report card

## Relationship Diagram (Summary)

```
Student ←→ Enrollment → Administrator/Teacher
Student ←→ Course (enrollment)
Student ←→ Course (attendance)
Student ←→ Course (grades)
Student ←→ Parent (linked)
Teacher → Course (assigned)
Teacher → Attendance (marked)
Teacher → Grade (recorded)
Course → Attendance (tracked)
Course → Grades (recorded)
```

---

## Required Relationship Queries (Examples)

| Query | Description |
|-------|-------------|
| Get all attendance for a student across all courses | Retrieve attendance records where student_id = ? |
| Get all grades for a student in a specific course | Retrieve grade records where student_id = ? AND course_id = ? |
| Get all students in a course | Retrieve enrollment records where course_id = ? |
| Get all courses taught by a teacher | Retrieve course records where teacher_id = ? |
| Get all parents linked to a student | Retrieve parent records linked to student_id = ? |
| Get attendance for a course on a specific date | Retrieve attendance records where course_id = ? AND date = ? |