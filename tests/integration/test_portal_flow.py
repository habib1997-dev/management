"""End-to-end integration: teacher teaches, grades recorded, parent logs in and views portal."""


def test_parent_portal_full_flow(client, db_session, make_auth_headers):
    admin = make_auth_headers(role="admin")

    # 1. Teacher created WITHOUT password and given a login later
    teacher = client.post(
        "/api/v1/teachers",
        json={
            "name": "Grace Hopper",
            "email": "grace.flow@schoolsystem.com",
            "subjects_taught": "Computer Science",
        },
        headers=admin,
    )
    assert teacher.status_code == 201
    tid = teacher.json()["teacher"]["teacher_id"]

    teacher_account = client.post(
        f"/api/v1/teachers/{tid}/account", json={"password": "teacherpw123"}, headers=admin
    )
    assert teacher_account.status_code == 201
    assert teacher_account.json()["account"]["role"] == "teacher"

    teacher_login = client.post(
        "/api/v1/auth/login",
        json={"email": "grace.flow@schoolsystem.com", "password": "teacherpw123"},
    )
    assert teacher_login.status_code == 200
    teacher_headers = {
        "Authorization": f"Bearer {teacher_login.json()['access_token']}"
    }

    # 2. Teacher creates a course with a student roster
    course = client.post(
        "/api/v1/courses",
        json={"name": "Algorithms", "grade_level": "10", "semester": "Fall 2026", "teacher_id": tid},
        headers=admin,
    )
    assert course.status_code == 201
    cid = course.json()["course"]["course_id"]

    student = client.post(
        "/api/v1/students",
        json={
            "first_name": "Zara",
            "last_name": "Ahmed",
            "date_of_birth": "2011-09-30",
            "grade_level": "10",
        },
        headers=admin,
    )
    assert student.status_code == 201
    sid = student.json()["student"]["student_id"]
    roster = client.put(
        f"/api/v1/courses/{cid}/students", json={"student_ids": [sid]}, headers=admin
    )
    assert roster.status_code == 200

    # 3. Teacher marks attendance and a grade (own course)
    att = client.post(
        "/api/v1/attendance",
        json={
            "course_id": cid,
            "date": "2026-09-07",
            "records": [{"student_id": sid, "status": "present"}],
        },
        headers=teacher_headers,
    )
    assert att.status_code == 201

    grade = client.post(
        "/api/v1/grades",
        json={
            "student_id": sid,
            "course_id": cid,
            "grade_value": 92.5,
            "assignment_type": "homework",
            "date_assigned": "2026-09-01",
            "date_due": "2026-09-05",
        },
        headers=teacher_headers,
    )
    assert grade.status_code == 201

    # 4. Admin links parent to the student and creates login for the parent WITH password
    parent = client.post(
        "/api/v1/parents",
        json={
            "name": "Fariha Ahmed",
            "email": "fariha.flow@family.net",
            "phone": "555-333-4444",
            "student_ids": [sid],
            "password": "parentpw123",
        },
        headers=admin,
    )
    assert parent.status_code == 201
    pid = parent.json()["parent"]["parent_id"]

    # 5. Parent logs in with their own password
    parent_login = client.post(
        "/api/v1/auth/login",
        json={"email": "fariha.flow@family.net", "password": "parentpw123"},
    )
    assert parent_login.status_code == 200
    assert parent_login.json()["role"] == "parent"
    parent_headers = {
        "Authorization": f"Bearer {parent_login.json()['access_token']}"
    }

    # 6. Parent views the portal and sees their child with attendance and grades
    portal = client.get(f"/api/v1/parents/{pid}/portal", headers=parent_headers)
    assert portal.status_code == 200
    body = portal.json()
    assert body["success"] is True
    children = body["parents"][0]["children"]
    assert len(children) == 1
    child = children[0]
    assert child["student_id"] == sid
    assert child["first_name"] == "Zara"
    assert child["grade_level"] == "10"
    assert child["attendance"][0]["course_id"] == cid
    assert child["attendance"][0]["date"] == "2026-09-07"
    assert child["attendance"][0]["status"] == "present"
    assert child["grades"][0]["grade_value"] == 92.5
    assert child["grades"][0]["assignment_type"] == "homework"

    # 7. Wrong password still rejected even though account exists
    bad = client.post(
        "/api/v1/auth/login",
        json={"email": "fariha.flow@family.net", "password": "wrongpass"},
    )
    assert bad.status_code == 401