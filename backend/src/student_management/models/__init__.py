"""Data models for the Student Management System.

Importing this package registers all tables on ``Base.metadata``.
"""

from student_management.models.associations import parent_students, student_courses
from student_management.models.attendance import Attendance
from student_management.models.course import Course
from student_management.models.enrollment import Enrollment
from student_management.models.grade import Grade
from student_management.models.parent import Parent
from student_management.models.student import Student
from student_management.models.teacher import Teacher
from student_management.models.user import User

__all__ = [
    "Attendance",
    "Course",
    "Enrollment",
    "Grade",
    "Parent",
    "Student",
    "Teacher",
    "User",
    "parent_students",
    "student_courses",
]