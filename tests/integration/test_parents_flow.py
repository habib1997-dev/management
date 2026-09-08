"""End-to-end integration: admin manages parents and links them to students."""


def test_full_parents_flow(client, db_session, make_auth_headers):
    admin = make_auth_headers(role="admin")

    # 1. Create two students
    sids = []
    for first, last in [("Ayesha", "Khan"), ("Bilal", "Khan")]:
        r = client.post(
            "/api/v1/students",
            json={
                "first_name": first,
                "last_name": last,
                "date_of_birth": "2012-06-15",
                "grade_level": "5",
            },
            headers=admin,
        )
        assert r.status_code == 201
        sids.append(r.json()["student"]["student_id"])

    # 2. Create a parent linked to both students
    parent_resp = client.post(
        "/api/v1/parents",
        json={
            "name": "Rashid Khan",
            "email": "rashid.integration@family.net",
            "phone": "555-111-2222",
            "student_ids": sids,
        },
        headers=admin,
    )
    assert parent_resp.status_code == 201
    assert parent_resp.json()["message"] == "Parent successfully created"
    pid = parent_resp.json()["parent"]["parent_id"]

    # 3. Parent shows in the parent list
    listing = client.get("/api/v1/parents", headers=admin)
    assert listing.status_code == 200
    assert any(p["parent_id"] == pid for p in listing.json()["data"])
    assert listing.json()["meta"]["total"] >= 1

    # 4. Both children are linked to the parent
    children = client.get(f"/api/v1/parents/{pid}/students", headers=admin)
    assert children.status_code == 200
    linked = {s["student_id"] for s in children.json()["data"]}
    assert linked == set(sids)

    # 5. A second parent created without children has an empty child list
    second = client.post(
        "/api/v1/parents",
        json={
            "name": "Unlinked Parent",
            "email": "unlinked.integration@family.net",
            "phone": "555-000-1111",
        },
        headers=admin,
    )
    assert second.status_code == 201
    empty_children = client.get(
        f"/api/v1/parents/{second.json()['parent']['parent_id']}/students", headers=admin
    )
    assert empty_children.json()["meta"]["total"] == 0

    # 6. Duplicate email rejected
    dup = client.post(
        "/api/v1/parents",
        json={
            "name": "Rashid Again",
            "email": "rashid.integration@family.net",
            "phone": "555-111-2222",
        },
        headers=admin,
    )
    assert dup.status_code == 400