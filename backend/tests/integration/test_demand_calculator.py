def test_demand_calculate_no_tasks_returns_zero_interval(client, make_organization):
    org = make_organization(code="ORG-DC-1")
    response = client.post(
        "/demand/calculate",
        json={
            "organization_id": org["id"],
            "start_time": "2026-01-01T08:00:00Z",
            "end_time": "2026-01-01T10:00:00Z",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["intervals"]) == 1
    assert body["intervals"][0]["target_demand"] == 0
    assert body["intervals"][0]["minimum_demand"] == 0


def test_demand_calculate_with_task_returns_expected_demand(client, make_organization, make_demand_task):
    org = make_organization(code="ORG-DC-2")
    make_demand_task(
        organization_id=org["id"],
        start_time="2026-01-01T08:30:00Z",
        duration_minutes=30,
        target_headcount=10,
        minimum_headcount=8,
    )

    response = client.post(
        "/demand/calculate",
        json={
            "organization_id": org["id"],
            "start_time": "2026-01-01T08:00:00Z",
            "end_time": "2026-01-01T10:00:00Z",
        },
    )
    assert response.status_code == 200
    body = response.json()
    demands = [interval["target_demand"] for interval in body["intervals"]]
    assert 10 in demands


def test_demand_calculate_end_time_before_start_time_rejected(client, make_organization):
    org = make_organization(code="ORG-DC-3")
    response = client.post(
        "/demand/calculate",
        json={
            "organization_id": org["id"],
            "start_time": "2026-01-01T10:00:00Z",
            "end_time": "2026-01-01T08:00:00Z",
        },
    )
    assert response.status_code == 422


def test_demand_calculate_filters_by_organization(client, make_organization, make_demand_task):
    org_a = make_organization(code="ORG-DC-4A")
    org_b = make_organization(code="ORG-DC-4B")

    make_demand_task(
        organization_id=org_a["id"],
        start_time="2026-01-01T08:30:00Z",
        duration_minutes=30,
        target_headcount=10,
        minimum_headcount=8,
    )

    response = client.post(
        "/demand/calculate",
        json={
            "organization_id": org_b["id"],
            "start_time": "2026-01-01T08:00:00Z",
            "end_time": "2026-01-01T10:00:00Z",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["intervals"]) == 1
    assert body["intervals"][0]["target_demand"] == 0