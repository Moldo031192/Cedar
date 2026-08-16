def test_create_employee_qualification(client, make_employee, make_qualification):
    employee = make_employee(employee_number="EMP-EQ-1", email="eq1@example.com")
    qualification = make_qualification(organization_id=employee["organization_id"], code="QUAL-EQ-1")

    response = client.post(
        "/employee-qualifications",
        json={
            "employee_id": employee["id"],
            "qualification_id": qualification["id"],
            "obtained_at": "2026-01-01",
            "status": "ACTIVE",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["employee_id"] == employee["id"]
    assert body["qualification_id"] == qualification["id"]
    assert body["status"] == "ACTIVE"


def test_create_employee_qualification_invalid_employee_rejected(client, make_qualification):
    qualification = make_qualification(code="QUAL-EQ-2")

    response = client.post(
        "/employee-qualifications",
        json={
            "employee_id": "11111111-1111-1111-1111-111111111111",
            "qualification_id": qualification["id"],
            "obtained_at": "2026-01-01",
            "status": "ACTIVE",
        },
    )
    assert response.status_code == 400


def test_create_employee_qualification_invalid_qualification_rejected(client, make_employee):
    employee = make_employee(employee_number="EMP-EQ-3", email="eq3@example.com")

    response = client.post(
        "/employee-qualifications",
        json={
            "employee_id": employee["id"],
            "qualification_id": "11111111-1111-1111-1111-111111111111",
            "obtained_at": "2026-01-01",
            "status": "ACTIVE",
        },
    )
    assert response.status_code == 400


def test_get_employee_qualification_not_found(client):
    response = client.get("/employee-qualifications/11111111-1111-1111-1111-111111111111")
    assert response.status_code == 404


def test_list_employee_qualifications(client, make_employee, make_qualification, make_employee_qualification):
    employee = make_employee(employee_number="EMP-EQ-4", email="eq4@example.com")
    qual_a = make_qualification(organization_id=employee["organization_id"], code="QUAL-EQ-4A")
    qual_b = make_qualification(organization_id=employee["organization_id"], code="QUAL-EQ-4B")

    make_employee_qualification(employee["id"], qual_a["id"])
    make_employee_qualification(employee["id"], qual_b["id"])

    response = client.get("/employee-qualifications")
    assert response.status_code == 200
    qualification_ids = {item["qualification_id"] for item in response.json()}
    assert {qual_a["id"], qual_b["id"]}.issubset(qualification_ids)


def test_update_employee_qualification(client, make_employee, make_qualification, make_employee_qualification):
    employee = make_employee(employee_number="EMP-EQ-5", email="eq5@example.com")
    qualification = make_qualification(organization_id=employee["organization_id"], code="QUAL-EQ-5")
    created = make_employee_qualification(employee["id"], qualification["id"], status="ACTIVE")

    response = client.put(
        f"/employee-qualifications/{created['id']}",
        json={"status": "SUSPENDED"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "SUSPENDED"


def test_update_employee_qualification_invalid_employee_rejected(
    client, make_employee, make_qualification, make_employee_qualification
):
    employee = make_employee(employee_number="EMP-EQ-6", email="eq6@example.com")
    qualification = make_qualification(organization_id=employee["organization_id"], code="QUAL-EQ-6")
    created = make_employee_qualification(employee["id"], qualification["id"])

    response = client.put(
        f"/employee-qualifications/{created['id']}",
        json={"employee_id": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 400


def test_update_employee_qualification_invalid_qualification_rejected(
    client, make_employee, make_qualification, make_employee_qualification
):
    employee = make_employee(employee_number="EMP-EQ-7", email="eq7@example.com")
    qualification = make_qualification(organization_id=employee["organization_id"], code="QUAL-EQ-7")
    created = make_employee_qualification(employee["id"], qualification["id"])

    response = client.put(
        f"/employee-qualifications/{created['id']}",
        json={"qualification_id": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 400


def test_delete_employee_qualification(client, make_employee, make_qualification, make_employee_qualification):
    employee = make_employee(employee_number="EMP-EQ-8", email="eq8@example.com")
    qualification = make_qualification(organization_id=employee["organization_id"], code="QUAL-EQ-8")
    created = make_employee_qualification(employee["id"], qualification["id"])

    response = client.delete(f"/employee-qualifications/{created['id']}")
    assert response.status_code == 200
    follow_up = client.get(f"/employee-qualifications/{created['id']}")
    assert follow_up.status_code == 404