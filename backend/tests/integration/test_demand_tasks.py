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
    # Untouched fields must remain exactly as before the partial update.
    assert body["target_headcount"] == 10
    assert body["minimum_headcount"] == 8