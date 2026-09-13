def test_create_shift(client, make_organization):
    org = make_organization(code="ORG-SH-1")
    response = client.post(
        "/shifts",
        json={
            "organization_id": org["id"],
            "name": "Morning Shift",
            "code": "SHIFT-MORNING",
            "start_time": "06:00:00",
            "end_time": "14:00:00",
            "crosses_midnight": False,
            "target_headcount": 14,
            "support_headcount": 5,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["code"] == "SHIFT-MORNING"
    assert body["start_time"] == "06:00:00"
    assert body["end_time"] == "14:00:00"
    assert body["crosses_midnight"] is False


def test_get_shift(client, make_shift):
    created = make_shift(code="SHIFT-GET")
    response = client.get(f"/shifts/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_shift_not_found(client):
    response = client.get("/shifts/11111111-1111-1111-1111-111111111111")
    assert response.status_code == 404


def test_list_shifts(client, make_organization, make_shift):
    org = make_organization(code="ORG-SH-LIST")
    make_shift(organization_id=org["id"], code="SHIFT-LIST-1")
    make_shift(organization_id=org["id"], code="SHIFT-LIST-2")
    response = client.get("/shifts")
    assert response.status_code == 200
    codes = {item["code"] for item in response.json()}
    assert {"SHIFT-LIST-1", "SHIFT-LIST-2"}.issubset(codes)


def test_update_shift(client, make_shift):
    shift = make_shift(code="SHIFT-UPDATE")
    response = client.put(
        f"/shifts/{shift['id']}",
        json={"name": "Renamed Shift"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed Shift"


def test_delete_shift(client, make_shift):
    shift = make_shift(code="SHIFT-DELETE")
    response = client.delete(f"/shifts/{shift['id']}")
    assert response.status_code == 200
    follow_up = client.get(f"/shifts/{shift['id']}")
    assert follow_up.status_code == 404


def test_create_shift_invalid_organization_rejected(client):
    response = client.post(
        "/shifts",
        json={
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "name": "Ghost Shift",
            "code": "SHIFT-GHOST",
            "start_time": "06:00:00",
            "end_time": "14:00:00",
        },
    )
    assert response.status_code == 400


def test_create_shift_duplicate_code_same_organization_rejected(client, make_organization, make_shift):
    org = make_organization(code="ORG-SH-DUP")
    make_shift(organization_id=org["id"], code="SHIFT-DUP")

    response = client.post(
        "/shifts",
        json={
            "organization_id": org["id"],
            "name": "Second Shift",
            "code": "SHIFT-DUP",
            "start_time": "14:00:00",
            "end_time": "22:00:00",
        },
    )
    assert response.status_code == 400


def test_create_shift_same_code_different_organizations_allowed(client, make_organization, make_shift):
    org_a = make_organization(code="ORG-SH-SAMECODE-A")
    org_b = make_organization(code="ORG-SH-SAMECODE-B")

    make_shift(organization_id=org_a["id"], code="SHIFT-SHARED")

    response = client.post(
        "/shifts",
        json={
            "organization_id": org_b["id"],
            "name": "Shift In Org B",
            "code": "SHIFT-SHARED",
            "start_time": "06:00:00",
            "end_time": "14:00:00",
        },
    )
    assert response.status_code == 201


def test_create_shift_invalid_time_combination_rejected(client, make_organization):
    org = make_organization(code="ORG-SH-INVALIDTIME")
    response = client.post(
        "/shifts",
        json={
            "organization_id": org["id"],
            "name": "Invalid Time Shift",
            "code": "SHIFT-INVALIDTIME",
            "start_time": "14:00:00",
            "end_time": "06:00:00",
            "crosses_midnight": False,
        },
    )
    assert response.status_code == 422


def test_create_shift_valid_crosses_midnight(client, make_organization):
    org = make_organization(code="ORG-SH-MIDNIGHT")
    response = client.post(
        "/shifts",
        json={
            "organization_id": org["id"],
            "name": "Night Shift",
            "code": "SHIFT-NIGHT",
            "start_time": "22:00:00",
            "end_time": "06:00:00",
            "crosses_midnight": True,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["crosses_midnight"] is True


def test_create_shift_equal_start_end_rejected(client, make_organization):
    org = make_organization(code="ORG-SH-EQUAL")
    response = client.post(
        "/shifts",
        json={
            "organization_id": org["id"],
            "name": "Equal Time Shift",
            "code": "SHIFT-EQUAL",
            "start_time": "06:00:00",
            "end_time": "06:00:00",
            "crosses_midnight": False,
        },
    )
    assert response.status_code == 422