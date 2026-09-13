def test_create_employee_shift(client, make_organization, make_employee, make_shift):
    org = make_organization(code="ORG-ES-1")
    employee = make_employee(organization_id=org["id"], employee_number="EMP-ES-1", email="es1@example.com")
    shift = make_shift(organization_id=org["id"], code="SHIFT-ES-1")

    response = client.post(
        "/employee-shifts",
        json={
            "employee_id": employee["id"],
            "shift_id": shift["id"],
            "work_date": "2026-01-05",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["employee_id"] == employee["id"]
    assert body["shift_id"] == shift["id"]
    assert body["work_date"] == "2026-01-05"
    assert body["is_present"] is True


def test_get_employee_shift(client, make_employee_shift):
    created = make_employee_shift()
    response = client.get(f"/employee-shifts/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_employee_shift_not_found(client):
    response = client.get("/employee-shifts/11111111-1111-1111-1111-111111111111")
    assert response.status_code == 404


def test_list_employee_shifts(client, make_organization, make_employee, make_shift, make_employee_shift):
    org = make_organization(code="ORG-ES-LIST")
    employee = make_employee(organization_id=org["id"], employee_number="EMP-ES-LIST", email="eslist@example.com")
    shift = make_shift(organization_id=org["id"], code="SHIFT-ES-LIST")

    make_employee_shift(employee_id=employee["id"], shift_id=shift["id"], work_date="2026-01-10")

    response = client.get("/employee-shifts")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert len(ids) >= 1


def test_update_employee_shift(client, make_employee_shift):
    created = make_employee_shift()
    response = client.put(
        f"/employee-shifts/{created['id']}",
        json={"notes": "Updated note"},
    )
    assert response.status_code == 200
    assert response.json()["notes"] == "Updated note"


def test_delete_employee_shift(client, make_employee_shift):
    created = make_employee_shift()
    response = client.delete(f"/employee-shifts/{created['id']}")
    assert response.status_code == 200
    follow_up = client.get(f"/employee-shifts/{created['id']}")
    assert follow_up.status_code == 404


def test_create_employee_shift_nonexistent_employee_rejected(client, make_organization, make_shift):
    org = make_organization(code="ORG-ES-NOEMP")
    shift = make_shift(organization_id=org["id"], code="SHIFT-ES-NOEMP")

    response = client.post(
        "/employee-shifts",
        json={
            "employee_id": "11111111-1111-1111-1111-111111111111",
            "shift_id": shift["id"],
            "work_date": "2026-01-05",
        },
    )
    assert response.status_code == 400


def test_create_employee_shift_nonexistent_shift_rejected(client, make_organization, make_employee):
    org = make_organization(code="ORG-ES-NOSHIFT")
    employee = make_employee(organization_id=org["id"], employee_number="EMP-ES-NOSHIFT", email="esnoshift@example.com")

    response = client.post(
        "/employee-shifts",
        json={
            "employee_id": employee["id"],
            "shift_id": "11111111-1111-1111-1111-111111111111",
            "work_date": "2026-01-05",
        },
    )
    assert response.status_code == 400


def test_create_employee_shift_organization_mismatch_rejected(client, make_organization, make_employee, make_shift):
    org_a = make_organization(code="ORG-ES-MISMATCH-A")
    org_b = make_organization(code="ORG-ES-MISMATCH-B")

    employee = make_employee(organization_id=org_a["id"], employee_number="EMP-ES-MISMATCH", email="esmismatch@example.com")
    shift = make_shift(organization_id=org_b["id"], code="SHIFT-ES-MISMATCH")

    response = client.post(
        "/employee-shifts",
        json={
            "employee_id": employee["id"],
            "shift_id": shift["id"],
            "work_date": "2026-01-05",
        },
    )
    assert response.status_code == 400


def test_create_employee_shift_duplicate_employee_date_rejected(client, make_organization, make_employee, make_shift):
    org = make_organization(code="ORG-ES-DUPDATE")
    employee = make_employee(organization_id=org["id"], employee_number="EMP-ES-DUPDATE", email="esdupdate@example.com")
    shift_a = make_shift(organization_id=org["id"], code="SHIFT-ES-DUPDATE-A")
    shift_b = make_shift(organization_id=org["id"], code="SHIFT-ES-DUPDATE-B")

    first = client.post(
        "/employee-shifts",
        json={"employee_id": employee["id"], "shift_id": shift_a["id"], "work_date": "2026-01-05"},
    )
    assert first.status_code == 201

    second = client.post(
        "/employee-shifts",
        json={"employee_id": employee["id"], "shift_id": shift_b["id"], "work_date": "2026-01-05"},
    )
    assert second.status_code == 400


def test_employee_shift_work_date_filter(client, make_organization, make_employee, make_shift):
    org = make_organization(code="ORG-ES-FILTER-1")
    employee = make_employee(organization_id=org["id"], employee_number="EMP-ES-FILTER-1", email="esfilter1@example.com")
    shift = make_shift(organization_id=org["id"], code="SHIFT-ES-FILTER-1")

    client.post(
        "/employee-shifts",
        json={"employee_id": employee["id"], "shift_id": shift["id"], "work_date": "2026-02-01"},
    )

    response = client.get("/employee-shifts", params={"work_date": "2026-02-01"})
    assert response.status_code == 200
    dates = {item["work_date"] for item in response.json()}
    assert dates == {"2026-02-01"}


def test_employee_shift_work_date_from_filter(client, make_organization, make_employee, make_shift):
    org = make_organization(code="ORG-ES-FILTER-2")
    employee = make_employee(organization_id=org["id"], employee_number="EMP-ES-FILTER-2", email="esfilter2@example.com")
    shift = make_shift(organization_id=org["id"], code="SHIFT-ES-FILTER-2")

    client.post(
        "/employee-shifts",
        json={"employee_id": employee["id"], "shift_id": shift["id"], "work_date": "2026-03-01"},
    )
    client.post(
        "/employee-shifts",
        json={"employee_id": employee["id"], "shift_id": shift["id"], "work_date": "2026-03-10"},
    )

    response = client.get("/employee-shifts", params={"employee_id": employee["id"], "work_date_from": "2026-03-05"})
    assert response.status_code == 200
    dates = {item["work_date"] for item in response.json()}
    assert dates == {"2026-03-10"}


def test_employee_shift_work_date_to_filter(client, make_organization, make_employee, make_shift):
    org = make_organization(code="ORG-ES-FILTER-3")
    employee = make_employee(organization_id=org["id"], employee_number="EMP-ES-FILTER-3", email="esfilter3@example.com")
    shift = make_shift(organization_id=org["id"], code="SHIFT-ES-FILTER-3")

    client.post(
        "/employee-shifts",
        json={"employee_id": employee["id"], "shift_id": shift["id"], "work_date": "2026-04-01"},
    )
    client.post(
        "/employee-shifts",
        json={"employee_id": employee["id"], "shift_id": shift["id"], "work_date": "2026-04-10"},
    )

    response = client.get("/employee-shifts", params={"employee_id": employee["id"], "work_date_to": "2026-04-05"})
    assert response.status_code == 200
    dates = {item["work_date"] for item in response.json()}
    assert dates == {"2026-04-01"}


def test_employee_shift_combined_filters(client, make_organization, make_department, make_role, make_employee, make_shift):
    org = make_organization(code="ORG-ES-FILTER-4")
    dept = make_department(organization_id=org["id"], code="DEPT-ES-FILTER-4")
    role = make_role(organization_id=org["id"], code="ROLE-ES-FILTER-4")

    employee_a = make_employee(
        organization_id=org["id"],
        department_id=dept["id"],
        role_id=role["id"],
        employee_number="EMP-ES-FILTER-4A",
        email="esfilter4a@example.com",
    )
    employee_b = make_employee(
        organization_id=org["id"],
        department_id=dept["id"],
        role_id=role["id"],
        employee_number="EMP-ES-FILTER-4B",
        email="esfilter4b@example.com",
    )
    shift = make_shift(organization_id=org["id"], code="SHIFT-ES-FILTER-4")

    client.post(
        "/employee-shifts",
        json={"employee_id": employee_a["id"], "shift_id": shift["id"], "work_date": "2026-05-01"},
    )
    client.post(
        "/employee-shifts",
        json={"employee_id": employee_b["id"], "shift_id": shift["id"], "work_date": "2026-05-01"},
    )

    response = client.get(
        "/employee-shifts",
        params={"shift_id": shift["id"], "employee_id": employee_a["id"], "work_date": "2026-05-01"},
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["employee_id"] == employee_a["id"]


def test_employee_shift_is_present_supported(client, make_organization, make_employee, make_shift):
    org = make_organization(code="ORG-ES-PRESENT")
    employee = make_employee(organization_id=org["id"], employee_number="EMP-ES-PRESENT", email="espresent@example.com")
    shift = make_shift(organization_id=org["id"], code="SHIFT-ES-PRESENT")

    response = client.post(
        "/employee-shifts",
        json={
            "employee_id": employee["id"],
            "shift_id": shift["id"],
            "work_date": "2026-01-05",
            "is_present": False,
        },
    )
    assert response.status_code == 201
    assert response.json()["is_present"] is False

    update_response = client.put(
        f"/employee-shifts/{response.json()['id']}",
        json={"is_present": True},
    )
    assert update_response.status_code == 200
    assert update_response.json()["is_present"] is True