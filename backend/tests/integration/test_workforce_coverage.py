def test_workforce_coverage_smoke(client, make_organization):
    org = make_organization(code="ORG-WC-1")
    response = client.post(
        "/workforce/coverage",
        json={
            "organization_id": org["id"],
            "start_time": "2026-01-01T08:00:00Z",
            "end_time": "2026-01-01T10:00:00Z",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["intervals"]) == 1
    assert body["eligible_employees"] == []


def test_workforce_coverage_only_active_employees_of_organization_included(
    client, make_organization, make_department, make_role, make_employee
):
    org_a = make_organization(code="ORG-WC-2A")
    org_b = make_organization(code="ORG-WC-2B")

    dept_a = make_department(organization_id=org_a["id"], code="DEPT-WC-2A")
    role_a = make_role(organization_id=org_a["id"], code="ROLE-WC-2A")
    dept_b = make_department(organization_id=org_b["id"], code="DEPT-WC-2B")
    role_b = make_role(organization_id=org_b["id"], code="ROLE-WC-2B")

    active_employee = make_employee(
        organization_id=org_a["id"],
        department_id=dept_a["id"],
        role_id=role_a["id"],
        employee_number="EMP-WC-ACTIVE",
        email="wc-active@example.com",
    )
    inactive_employee = make_employee(
        organization_id=org_a["id"],
        department_id=dept_a["id"],
        role_id=role_a["id"],
        employee_number="EMP-WC-INACTIVE",
        email="wc-inactive@example.com",
    )
    other_org_employee = make_employee(
        organization_id=org_b["id"],
        department_id=dept_b["id"],
        role_id=role_b["id"],
        employee_number="EMP-WC-OTHERORG",
        email="wc-otherorg@example.com",
    )

    deactivate_response = client.put(
        f"/employees/{inactive_employee['id']}",
        json={"is_active": False},
    )
    assert deactivate_response.status_code == 200

    response = client.post(
        "/workforce/coverage",
        json={
            "organization_id": org_a["id"],
            "start_time": "2026-01-01T08:00:00Z",
            "end_time": "2026-01-01T10:00:00Z",
        },
    )
    assert response.status_code == 200
    employee_numbers = {item["employee_number"] for item in response.json()["eligible_employees"]}

    assert "EMP-WC-ACTIVE" in employee_numbers
    assert "EMP-WC-INACTIVE" not in employee_numbers
    assert "EMP-WC-OTHERORG" not in employee_numbers


def test_workforce_coverage_end_time_before_start_time_rejected(client, make_organization):
    org = make_organization(code="ORG-WC-3")
    response = client.post(
        "/workforce/coverage",
        json={
            "organization_id": org["id"],
            "start_time": "2026-01-01T10:00:00Z",
            "end_time": "2026-01-01T08:00:00Z",
        },
    )
    assert response.status_code == 422


def test_workforce_coverage_eligible_employee_full_db_chain(
    client,
    make_organization,
    make_employee,
    make_qualification,
    make_employee_qualification,
    make_demand_task,
):
    org = make_organization(code="ORG-WC-4")
    employee = make_employee(
        organization_id=org["id"], employee_number="EMP-WC-ELIGIBLE", email="wc-eligible@example.com"
    )
    qualification = make_qualification(organization_id=org["id"], code="QUAL-WC-4")
    make_employee_qualification(employee["id"], qualification["id"], status="ACTIVE")
    make_demand_task(
        organization_id=org["id"],
        start_time="2026-01-01T08:30:00Z",
        duration_minutes=30,
        required_qualification_ids=[qualification["id"]],
    )

    response = client.post(
        "/workforce/coverage",
        json={
            "organization_id": org["id"],
            "start_time": "2026-01-01T08:00:00Z",
            "end_time": "2026-01-01T10:00:00Z",
        },
    )
    assert response.status_code == 200
    eligible_employees = response.json()["eligible_employees"]
    assert len(eligible_employees) == 1
    assert eligible_employees[0]["employee_number"] == "EMP-WC-ELIGIBLE"
    assert eligible_employees[0]["eligible"] is True
    assert eligible_employees[0]["missing_qualification_ids"] == []


def test_workforce_coverage_ineligible_employee_missing_qualification(
    client,
    make_organization,
    make_employee,
    make_qualification,
    make_demand_task,
):
    org = make_organization(code="ORG-WC-5")
    employee = make_employee(
        organization_id=org["id"], employee_number="EMP-WC-MISSING", email="wc-missing@example.com"
    )
    qualification = make_qualification(organization_id=org["id"], code="QUAL-WC-5")
    make_demand_task(
        organization_id=org["id"],
        start_time="2026-01-01T08:30:00Z",
        duration_minutes=30,
        required_qualification_ids=[qualification["id"]],
    )

    response = client.post(
        "/workforce/coverage",
        json={
            "organization_id": org["id"],
            "start_time": "2026-01-01T08:00:00Z",
            "end_time": "2026-01-01T10:00:00Z",
        },
    )
    assert response.status_code == 200
    eligible_employees = response.json()["eligible_employees"]
    assert len(eligible_employees) == 1
    assert eligible_employees[0]["employee_number"] == "EMP-WC-MISSING"
    assert eligible_employees[0]["eligible"] is False
    assert eligible_employees[0]["missing_qualification_ids"] == [qualification["id"]]