"""End-to-end integration: teacher records grades for students in their course."""


def test_full_grades_flow(client, db_session, make_auth_headers):
    admin = make_auth_headers(role="admin")

    # 1. Create teacher + course + students + roster
    teacher_resp = client.post(
        "/api/v1/teachers",
        json={
            "name": "Grace Hopper",
            "email": "grace.integration@schoolsystem.com",
            "subjects_taught": "Computer Science",
        },
        headers=admin,
    )
    assert teacher_resp.status_code == 201
    tid = teacher_resp.json()["teacher"]["teacher_id"]

    teacher = make_auth_headers(role="teacher", teacher_id=tid)

    course = client.post(
        "/api/v1/courses",
        json={
            "name": "Intro to CS",
            "teacher_id": tid,
            "grade_level": "11",
            "semester": "Fall 2026",
        },
        headers=admin,
    )
    assert course.status_code == 201
    cid = course.json()["course"]["course_id"]

    sids = []
    for first, last in [("Alan", "Turing"), ("Ada", "Byron")]:
        r = client.post(
            "/api/v1/students",
            json={
                "first_name": first,
                "last_name": last,
                "date_of_birth": "2011-04-15",
                "grade_level": "11",
            },
            headers=admin,
        )
        sids.append(r.json()["student"]["student_id"])

    client.put(f"/api/v1/courses/{cid}/students", json={"student_ids": sids}, headers=admin)

    # 2. Record grades for both students (quiz + final)
    quiz = client.post(
        "/api/v1/grades",
        json={
            "student_id": sids[0],
            "course_id": cid,
            "grade_value": 88.0,
            "assignment_type": "quiz",
            "date_assigned": "2026-09-01",
            "date_due": "2026-09-04",
        },
        headers=teacher,
    )
    assert quiz.status_code == 201
    assert quiz.json()["message"] == "Grade successfully recorded"

    final = client.post(
        "/api/v1/grades",
        json={
            "student_id": sids[1],
            "course_id": cid,
            "grade_value": 97.5,
            "assignment_type": "final",
            "date_assigned": "2026-09-20",
            "date_due": "2026-09-25",
        },
        headers=teacher,
    )
    assert final.status_code == 201
    assert final.json()["grade"]["grade_value"] == 97.5
    # date_graded falls back to date_due when it is in the future
    assert final.json()["grade"]["date_graded"] == "2026-09-25"

    # 3. View course grades
    course_grades = client.get(f"/api/v1/courses/{cid}/grades", headers=teacher)
    assert course_grades.status_code == 200
    assert course_grades.json()["meta"]["total"] == 2

    # 4. View individual student grades with course filter
    student_grades = client.get(f"/api/v1/students/{sids[0]}/grades", headers=teacher)
    assert student_grades.status_code == 200
    assert student_grades.json()["meta"]["total"] == 1
    assert student_grades.json()["data"][0]["assignment_type"] == "quiz"

    filtered = client.get(
        f"/api/v1/students/{sids[0]}/grades?courseId={cid}", headers=teacher
    )
    assert filtered.json()["meta"]["total"] == 1

    # 5. Invalid grade rejected and not stored
    before = client.get(f"/api/v1/courses/{cid}/grades", headers=admin).json()["meta"]["total"]
    bad = client.post(
        "/api/v1/grades",
        json={
            "student_id": sids[0],
            "course_id": cid,
            "grade_value": 150,
            "assignment_type": "test",
            "date_assigned": "2026-09-01",
            "date_due": "2026-09-05",
        },
        headers=teacher,
    )
    assert bad.status_code == 422
    after = client.get(f"/api/v1/courses/{cid}/grades", headers=admin).json()["meta"]["total"]
    assert after == before

    # 6. Admin can record grades on any course
    admin_grade = client.post(
        "/api/v1/grades",
        json={
            "student_id": sids[0],
            "course_id": cid,
            "grade_value": 91.0,
            "assignment_type": "homework",
            "date_assigned": "2026-09-02",
            "date_due": "2026-09-06",
        },
        headers=admin,
    )
    assert admin_grade.status_code == 201
    assert admin_grade.json()["grade"]["assignment_type"] == "homework"