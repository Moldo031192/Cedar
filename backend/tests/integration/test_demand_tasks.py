def test_create_demand_task(client, make_organization):
    org = make_organization(code="ORG-DT-1")
    response = client.post(
        "/demand-tasks",
        json={
            "organization_id": org["id"],
            "flight_reference": "FL-200",
            "task_type": "TURNAROUND",
            "start_time": "2026-01-01T08:00:00Z",
            "duration_minutes": 45,
            "target_headcount": 12,
            "minimum_headcount": 10,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["flight_reference"] == "FL-200"
    assert body["target_headcount"] == 12
    assert body["minimum_headcount"] == 10


def test_update_demand_task_negative_target_headcount_rejected(client, make_demand_task):
    task = make_demand_task()
    response = client.put(
        f"/demand-tasks/{task['id']}",
        json={"target_headcount": -5},
    )
    assert response.status_code == 422


def test_update_demand_task_negative_minimum_headcount_rejected(client, make_demand_task):
    task = make_demand_task()
    response = client.put(
        f"/demand-tasks/{task['id']}",
        json={"minimum_headcount": -1},
    )
    assert response.status_code == 422


def test_update_demand_task_valid_partial_update_still_works(client, make_demand_task):
    task = make_demand_task(target_headcount=10, minimum_headcount=8)
    response = client.put(
        f"/demand-tasks/{task['id']}",
        json={"flight_reference": "FL-UPDATED"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["flight_reference"] == "FL-UPDATED"
    assert body["target_headcount"] == 10
    assert body["minimum_headcount"] == 8


def test_create_demand_task_with_required_qualifications(client, make_organization, make_qualification):
    org = make_organization(code="ORG-DT-QUAL-1")
    qual = make_qualification(organization_id=org["id"], code="QUAL-DT-1")

    response = client.post(
        "/demand-tasks",
        json={
            "organization_id": org["id"],
            "flight_reference": "FL-QUAL",
            "task_type": "TURNAROUND",
            "start_time": "2026-01-01T08:00:00Z",
            "duration_minutes": 60,
            "target_headcount": 10,
            "minimum_headcount": 8,
            "required_qualification_ids": [qual["id"]],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["required_qualification_ids"] == [qual["id"]]


def test_create_demand_task_invalid_qualification_id_rejected(client, make_organization):
    org = make_organization(code="ORG-DT-QUAL-2")
    response = client.post(
        "/demand-tasks",
        json={
            "organization_id": org["id"],
            "flight_reference": "FL-BADQUAL",
            "task_type": "TURNAROUND",
            "start_time": "2026-01-01T08:00:00Z",
            "duration_minutes": 60,
            "target_headcount": 10,
            "minimum_headcount": 8,
            "required_qualification_ids": ["11111111-1111-1111-1111-111111111111"],
        },
    )
    assert response.status_code == 400


def test_create_demand_task_invalid_organization_rejected(client):
    response = client.post(
        "/demand-tasks",
        json={
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "flight_reference": "FL-BADORG",
            "task_type": "TURNAROUND",
            "start_time": "2026-01-01T08:00:00Z",
            "duration_minutes": 60,
            "target_headcount": 10,
            "minimum_headcount": 8,
        },
    )
    assert response.status_code == 400


def test_create_demand_task_duration_not_positive_rejected(client, make_organization):
    org = make_organization(code="ORG-DT-DUR")
    response = client.post(
        "/demand-tasks",
        json={
            "organization_id": org["id"],
            "flight_reference": "FL-DUR",
            "task_type": "TURNAROUND",
            "start_time": "2026-01-01T08:00:00Z",
            "duration_minutes": 0,
            "target_headcount": 10,
            "minimum_headcount": 8,
        },
    )
    assert response.status_code == 422


def test_create_demand_task_minimum_greater_than_target_rejected(client, make_organization):
    org = make_organization(code="ORG-DT-MINMAX")
    response = client.post(
        "/demand-tasks",
        json={
            "organization_id": org["id"],
            "flight_reference": "FL-MINMAX",
            "task_type": "TURNAROUND",
            "start_time": "2026-01-01T08:00:00Z",
            "duration_minutes": 60,
            "target_headcount": 5,
            "minimum_headcount": 10,
        },
    )
    assert response.status_code == 422


def test_update_demand_task_duration_not_positive_rejected(client, make_demand_task):
    task = make_demand_task()
    response = client.put(
        f"/demand-tasks/{task['id']}",
        json={"duration_minutes": 0},
    )
    assert response.status_code == 400


def test_update_demand_task_minimum_greater_than_target_rejected(client, make_demand_task):
    task = make_demand_task(target_headcount=10, minimum_headcount=8)
    response = client.put(
        f"/demand-tasks/{task['id']}",
        json={"minimum_headcount": 15},
    )
    assert response.status_code == 400


def test_update_demand_task_invalid_organization_rejected(client, make_demand_task):
    task = make_demand_task()
    response = client.put(
        f"/demand-tasks/{task['id']}",
        json={"organization_id": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 400


def test_update_demand_task_required_qualification_ids_none_leaves_unchanged(
    client, make_organization, make_qualification
):
    org = make_organization(code="ORG-DT-QUAL-NONE")
    qual = make_qualification(organization_id=org["id"], code="QUAL-DT-NONE")

    created = client.post(
        "/demand-tasks",
        json={
            "organization_id": org["id"],
            "flight_reference": "FL-NONE",
            "task_type": "TURNAROUND",
            "start_time": "2026-01-01T08:00:00Z",
            "duration_minutes": 60,
            "target_headcount": 10,
            "minimum_headcount": 8,
            "required_qualification_ids": [qual["id"]],
        },
    ).json()

    response = client.put(
        f"/demand-tasks/{created['id']}",
        json={"flight_reference": "FL-NONE-UPDATED"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["required_qualification_ids"] == [qual["id"]]


def test_update_demand_task_required_qualification_ids_empty_list_clears(
    client, make_organization, make_qualification
):
    org = make_organization(code="ORG-DT-QUAL-CLEAR")
    qual = make_qualification(organization_id=org["id"], code="QUAL-DT-CLEAR")

    created = client.post(
        "/demand-tasks",
        json={
            "organization_id": org["id"],
            "flight_reference": "FL-CLEAR",
            "task_type": "TURNAROUND",
            "start_time": "2026-01-01T08:00:00Z",
            "duration_minutes": 60,
            "target_headcount": 10,
            "minimum_headcount": 8,
            "required_qualification_ids": [qual["id"]],
        },
    ).json()

    response = client.put(
        f"/demand-tasks/{created['id']}",
        json={"required_qualification_ids": []},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["required_qualification_ids"] == []


def test_update_demand_task_required_qualification_ids_invalid_rejected(client, make_demand_task):
    task = make_demand_task()
    response = client.put(
        f"/demand-tasks/{task['id']}",
        json={"required_qualification_ids": ["11111111-1111-1111-1111-111111111111"]},
    )
    assert response.status_code == 400


def test_get_demand_task_not_found(client):
    response = client.get("/demand-tasks/11111111-1111-1111-1111-111111111111")
    assert response.status_code == 404


def test_list_demand_tasks(client, make_organization, make_demand_task):
    org = make_organization(code="ORG-DT-LIST")
    make_demand_task(organization_id=org["id"], flight_reference="FL-LIST-1")
    make_demand_task(organization_id=org["id"], flight_reference="FL-LIST-2")
    response = client.get("/demand-tasks")
    assert response.status_code == 200
    refs = {item["flight_reference"] for item in response.json()}
    assert {"FL-LIST-1", "FL-LIST-2"}.issubset(refs)


def test_delete_demand_task(client, make_demand_task):
    task = make_demand_task(flight_reference="FL-DELETE")
    response = client.delete(f"/demand-tasks/{task['id']}")
    assert response.status_code == 200
    follow_up = client.get(f"/demand-tasks/{task['id']}")
    assert follow_up.status_code == 404


def test_demand_task_end_time_computed_correctly(client, make_organization):
    from datetime import datetime, timedelta

    org = make_organization(code="ORG-DT-ENDTIME")
    response = client.post(
        "/demand-tasks",
        json={
            "organization_id": org["id"],
            "flight_reference": "FL-ENDTIME",
            "task_type": "TURNAROUND",
            "start_time": "2026-01-01T08:00:00Z",
            "duration_minutes": 90,
            "target_headcount": 10,
            "minimum_headcount": 8,
        },
    )
    assert response.status_code == 201
    body = response.json()
    start = datetime.fromisoformat(body["start_time"])
    end = datetime.fromisoformat(body["end_time"])
    assert end - start == timedelta(minutes=90)