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
    assert body["intervals"][0]["scheduled_workforce"] == 0
    assert body["task_eligibility"] == []


def test_workforce_coverage_end_time_before_start_time_rejected(client, make_organization):
    org = make_organization(code="ORG-WC-2")
    response = client.post(
        "/workforce/coverage",
        json={
            "organization_id": org["id"],
            "start_time": "2026-01-01T10:00:00Z",
            "end_time": "2026-01-01T08:00:00Z",
        },
    )
    assert response.status_code == 422


def test_workforce_coverage_active_present_overlapping_counts(
    client, make_organization, make_employee, make_shift, make_employee_shift
):
    org = make_organization(code="ORG-WC-3")
    employee = make_employee(organization_id=org["id"], employee_number="EMP-WC-3", email="wc3@example.com")
    shift = make_shift(organization_id=org["id"], code="SHIFT-WC-3", start_time="06:00:00", end_time="14:00:00")
    make_employee_shift(employee_id=employee["id"], shift_id=shift["id"], work_date="2026-01-01")

    response = client.post(
        "/workforce/coverage",
        json={
            "organization_id": org["id"],
            "start_time": "2026-01-01T08:00:00Z",
            "end_time": "2026-01-01T10:00:00Z",
        },
    )
    assert response.status_code == 200
    assert response.json()["intervals"][0]["scheduled_workforce"] == 1


def test_workforce_coverage_absent_shift_does_not_count(
    client, make_organization, make_employee, make_shift, make_employee_shift
):
    org = make_organization(code="ORG-WC-4")
    employee = make_employee(organization_id=org["id"], employee_number="EMP-WC-4", email="wc4@example.com")
    shift = make_shift(organization_id=org["id"], code="SHIFT-WC-4", start_time="06:00:00", end_time="14:00:00")
    make_employee_shift(
        employee_id=employee["id"], shift_id=shift["id"], work_date="2026-01-01", is_present=False
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
    assert response.json()["intervals"][0]["scheduled_workforce"] == 0


def test_workforce_coverage_inactive_employee_does_not_count(
    client, make_organization, make_employee, make_shift, make_employee_shift
):
    org = make_organization(code="ORG-WC-5")
    employee = make_employee(organization_id=org["id"], employee_number="EMP-WC-5", email="wc5@example.com")
    shift = make_shift(organization_id=org["id"], code="SHIFT-WC-5", start_time="06:00:00", end_time="14:00:00")
    make_employee_shift(employee_id=employee["id"], shift_id=shift["id"], work_date="2026-01-01")

    deactivate = client.put(f"/employees/{employee['id']}", json={"is_active": False})
    assert deactivate.status_code == 200

    response = client.post(
        "/workforce/coverage",
        json={
            "organization_id": org["id"],
            "start_time": "2026-01-01T08:00:00Z",
            "end_time": "2026-01-01T10:00:00Z",
        },
    )
    assert response.status_code == 200
    assert response.json()["intervals"][0]["scheduled_workforce"] == 0


def test_workforce_coverage_non_overlapping_shift_does_not_count(
    client, make_organization, make_employee, make_shift, make_employee_shift
):
    org = make_organization(code="ORG-WC-6")
    employee = make_employee(organization_id=org["id"], employee_number="EMP-WC-6", email="wc6@example.com")
    shift = make_shift(organization_id=org["id"], code="SHIFT-WC-6", start_time="16:00:00", end_time="22:00:00")
    make_employee_shift(employee_id=employee["id"], shift_id=shift["id"], work_date="2026-01-01")

    response = client.post(
        "/workforce/coverage",
        json={
            "organization_id": org["id"],
            "start_time": "2026-01-01T08:00:00Z",
            "end_time": "2026-01-01T10:00:00Z",
        },
    )
    assert response.status_code == 200
    assert response.json()["intervals"][0]["scheduled_workforce"] == 0


def test_workforce_coverage_organization_isolation(
    client, make_organization, make_employee, make_shift, make_employee_shift
):
    org_a = make_organization(code="ORG-WC-7A")
    org_b = make_organization(code="ORG-WC-7B")

    employee_a = make_employee(organization_id=org_a["id"], employee_number="EMP-WC-7A", email="wc7a@example.com")
    shift_a = make_shift(organization_id=org_a["id"], code="SHIFT-WC-7A", start_time="06:00:00", end_time="14:00:00")
    make_employee_shift(employee_id=employee_a["id"], shift_id=shift_a["id"], work_date="2026-01-01")

    response = client.post(
        "/workforce/coverage",
        json={
            "organization_id": org_b["id"],
            "start_time": "2026-01-01T08:00:00Z",
            "end_time": "2026-01-01T10:00:00Z",
        },
    )
    assert response.status_code == 200
    assert response.json()["intervals"][0]["scheduled_workforce"] == 0


def test_workforce_coverage_midnight_crossing_shift(
    client, make_organization, make_employee, make_shift, make_employee_shift
):
    org = make_organization(code="ORG-WC-8")
    employee = make_employee(organization_id=org["id"], employee_number="EMP-WC-8", email="wc8@example.com")
    shift = make_shift(
        organization_id=org["id"],
        code="SHIFT-WC-8",
        start_time="22:00:00",
        end_time="06:00:00",
        crosses_midnight=True,
    )
    make_employee_shift(employee_id=employee["id"], shift_id=shift["id"], work_date="2026-01-01")

    response = client.post(
        "/workforce/coverage",
        json={
            "organization_id": org["id"],
            "start_time": "2026-01-02T02:00:00Z",
            "end_time": "2026-01-02T04:00:00Z",
        },
    )
    assert response.status_code == 200
    assert response.json()["intervals"][0]["scheduled_workforce"] == 1


def test_workforce_coverage_task_eligibility_full_db_chain(
    client,
    make_organization,
    make_employee,
    make_qualification,
    make_employee_qualification,
    make_shift,
    make_employee_shift,
    make_demand_task,
):
    org = make_organization(code="ORG-WC-9")
    employee = make_employee(
        organization_id=org["id"], employee_number="EMP-WC-ELIGIBLE", email="wc9-eligible@example.com"
    )
    qualification = make_qualification(organization_id=org["id"], code="QUAL-WC-9")
    make_employee_qualification(employee["id"], qualification["id"], status="ACTIVE")
    shift = make_shift(organization_id=org["id"], code="SHIFT-WC-9", start_time="06:00:00", end_time="14:00:00")
    make_employee_shift(employee_id=employee["id"], shift_id=shift["id"], work_date="2026-01-01")

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
    task_eligibility = response.json()["task_eligibility"]
    assert len(task_eligibility) == 1
    employees = task_eligibility[0]["employees"]
    assert len(employees) == 1
    assert employees[0]["employee_number"] == "EMP-WC-ELIGIBLE"
    assert employees[0]["eligible"] is True
    assert employees[0]["missing_qualification_ids"] == []


def test_workforce_coverage_task_eligibility_missing_qualification(
    client,
    make_organization,
    make_employee,
    make_qualification,
    make_shift,
    make_employee_shift,
    make_demand_task,
):
    org = make_organization(code="ORG-WC-10")
    employee = make_employee(
        organization_id=org["id"], employee_number="EMP-WC-MISSING", email="wc10-missing@example.com"
    )
    qualification = make_qualification(organization_id=org["id"], code="QUAL-WC-10")
    shift = make_shift(organization_id=org["id"], code="SHIFT-WC-10", start_time="06:00:00", end_time="14:00:00")
    make_employee_shift(employee_id=employee["id"], shift_id=shift["id"], work_date="2026-01-01")

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
    employees = response.json()["task_eligibility"][0]["employees"]
    assert len(employees) == 1
    assert employees[0]["employee_number"] == "EMP-WC-MISSING"
    assert employees[0]["eligible"] is False
    assert employees[0]["missing_qualification_ids"] == [qualification["id"]]


def test_workforce_coverage_employee_without_shift_not_in_task_eligibility(
    client,
    make_organization,
    make_employee,
    make_qualification,
    make_demand_task,
):
    org = make_organization(code="ORG-WC-11")
    make_employee(organization_id=org["id"], employee_number="EMP-WC-NOSHIFT", email="wc11-noshift@example.com")
    qualification = make_qualification(organization_id=org["id"], code="QUAL-WC-11")

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
    task_eligibility = response.json()["task_eligibility"]
    assert len(task_eligibility) == 1
    assert task_eligibility[0]["employees"] == []