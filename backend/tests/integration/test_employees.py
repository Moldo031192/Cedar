def test_create_employee(client, make_organization, make_department, make_role):
    org = make_organization(code="ORG-EMP-1")
    dept = make_department(organization_id=org["id"], code="DEPT-EMP-1")
    role = make_role(organization_id=org["id"], code="ROLE-EMP-1")

    response = client.post(
        "/employees",
        json={
            "organization_id": org["id"],
            "department_id": dept["id"],
            "role_id": role["id"],
            "employee_number": "EMP-100",
            "first_name": "Ana",
            "last_name": "Pop",
            "email": "ana.pop@example.com",
            "employment_type": "FULL_TIME",
            "hire_date": "2026-01-01",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["employee_number"] == "EMP-100"
    assert body["email"] == "ana.pop@example.com"


def test_create_employee_invalid_organization_rejected(client, make_organization, make_department, make_role):
    org = make_organization(code="ORG-EMP-INVALID")
    dept = make_department(organization_id=org["id"], code="DEPT-EMP-INVALID")
    role = make_role(organization_id=org["id"], code="ROLE-EMP-INVALID")

    response = client.post(
        "/employees",
        json={
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "department_id": dept["id"],
            "role_id": role["id"],
            "employee_number": "EMP-INVALID",
            "first_name": "Ana",
            "last_name": "Pop",
            "email": "ana.invalid@example.com",
            "employment_type": "FULL_TIME",
            "hire_date": "2026-01-01",
        },
    )
    assert response.status_code == 400


def test_create_employee_duplicate_employee_number_rejected(client, make_organization, make_department, make_role):
    org = make_organization(code="ORG-EMP-DUP")
    dept = make_department(organization_id=org["id"], code="DEPT-EMP-DUP")
    role = make_role(organization_id=org["id"], code="ROLE-EMP-DUP")

    payload = {
        "organization_id": org["id"],
        "department_id": dept["id"],
        "role_id": role["id"],
        "employee_number": "EMP-DUP",
        "first_name": "Ana",
        "last_name": "Pop",
        "email": "first@example.com",
        "employment_type": "FULL_TIME",
        "hire_date": "2026-01-01",
    }
    first = client.post("/employees", json=payload)
    assert first.status_code == 201

    second_payload = dict(payload, email="second@example.com")
    second = client.post("/employees", json=second_payload)
    assert second.status_code == 400


def test_create_employee_duplicate_email_rejected(client, make_organization, make_department, make_role):
    org = make_organization(code="ORG-EMP-DUP-EMAIL")
    dept = make_department(organization_id=org["id"], code="DEPT-EMP-DUP-EMAIL")
    role = make_role(organization_id=org["id"], code="ROLE-EMP-DUP-EMAIL")

    payload = {
        "organization_id": org["id"],
        "department_id": dept["id"],
        "role_id": role["id"],
        "employee_number": "EMP-EMAIL-1",
        "first_name": "Ana",
        "last_name": "Pop",
        "email": "shared@example.com",
        "employment_type": "FULL_TIME",
        "hire_date": "2026-01-01",
    }
    first = client.post("/employees", json=payload)
    assert first.status_code == 201

    second_payload = dict(payload, employee_number="EMP-EMAIL-2")
    second = client.post("/employees", json=second_payload)
    assert second.status_code == 400


def test_get_employee_not_found(client):
    response = client.get("/employees/11111111-1111-1111-1111-111111111111")
    assert response.status_code == 404


def test_update_employee(client, make_employee):
    employee = make_employee(employee_number="EMP-UPDATE", email="update@example.com")
    response = client.put(f"/employees/{employee['id']}", json={"first_name": "Maria"})
    assert response.status_code == 200
    assert response.json()["first_name"] == "Maria"


def test_delete_employee(client, make_employee):
    employee = make_employee(employee_number="EMP-DELETE", email="delete@example.com")
    response = client.delete(f"/employees/{employee['id']}")
    assert response.status_code == 200
    follow_up = client.get(f"/employees/{employee['id']}")
    assert follow_up.status_code == 404

