"""End-to-end integration: teacher marks attendance for students in their course."""


def test_full_attendance_flow(client, db_session, make_auth_headers):
    admin = make_auth_headers(role="admin")

    # 1. Create teacher
    teacher_resp = client.post(
        "/api/v1/teachers",
        json={
            "name": "Jane Smith",
            "email": "jane.integration@schoolsystem.com",
            "subjects_taught": "Mathematics",
        },
        headers=admin,
    )
    assert teacher_resp.status_code == 201
    tid = teacher_resp.json()["teacher"]["teacher_id"]

    # 2. Create teacher user
    teacher = make_auth_headers(role="teacher", teacher_id=tid)

    # 3. Create course + assign students
    course = client.post(
        "/api/v1/courses",
        json={"name": "Algebra II", "teacher_id": tid, "grade_level": "10", "semester": "Fall 2026"},
        headers=admin,
    )
    assert course.status_code == 201
    cid = course.json()["course"]["course_id"]

    sids = []
    for first, last in [("John", "Doe"), ("Maria", "Garcia")]:
        r = client.post(
            "/api/v1/students",
            json={"first_name": first, "last_name": last, "date_of_birth": "2009-03-20", "grade_level": "10"},
            headers=admin,
        )
        sids.append(r.json()["student"]["student_id"])

    client.put(f"/api/v1/courses/{cid}/students", json={"student_ids": sids}, headers=admin)

    # 4. Teacher marks attendance (today)
    marked = client.post(
        "/api/v1/attendance",
        json={
            "course_id": cid,
            "date": "2026-09-07",
            "records": [
                {"student_id": sids[0], "status": "present"},
                {"student_id": sids[1], "status": "absent"},
            ],
        },
        headers=teacher,
    )
    assert marked.status_code == 201
    assert {r["status"] for r in marked.json()["attendance"]} == {"present", "absent"}

    # 5. View course attendance
    course_att = client.get(f"/api/v1/attendance/{cid}", headers=teacher)
    assert course_att.status_code == 200
    assert course_att.json()["meta"]["total"] == 2

    # 6. View individual student attendance
    student_att = client.get(f"/api/v1/students/{sids[0]}/attendance", headers=teacher)
    assert student_att.status_code == 200
    assert student_att.json()["data"][0]["status"] == "present"

    # 7. Re-mark same day (upsert)
    updated = client.post(
        "/api/v1/attendance",
        json={
            "course_id": cid,
            "date": "2026-09-07",
            "records": [{"student_id": sids[1], "status": "late"}],
        },
        headers=teacher,
    )
    assert updated.status_code == 201
    assert updated.json()["attendance"][0]["status"] == "late"

    # 8. Confirm total unchanged after upsert
    verify = client.get(f"/api/v1/attendance/{cid}", headers=teacher)
    assert verify.json()["meta"]["total"] == 2