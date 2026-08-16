def test_create_department(client, make_organization):
    org = make_organization(code="ORG-DEPT-1")
    response = client.post(
        "/departments",
        json={"organization_id": org["id"], "name": "Ramp Ops", "code": "DEPT-RAMP"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["organization_id"] == org["id"]
    assert body["code"] == "DEPT-RAMP"


def test_create_department_invalid_organization_rejected(client):
    response = client.post(
        "/departments",
        json={
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "name": "Ghost Dept",
            "code": "DEPT-GHOST",
        },
    )
    assert response.status_code == 400


def test_create_department_duplicate_code_rejected(client, make_organization, make_department):
    org = make_organization(code="ORG-DEPT-2")
    make_department(organization_id=org["id"], code="DEPT-DUP")
    response = client.post(
        "/departments",
        json={"organization_id": org["id"], "name": "Second Dept", "code": "DEPT-DUP"},
    )
    assert response.status_code == 400


def test_get_department_not_found(client):
    response = client.get("/departments/11111111-1111-1111-1111-111111111111")
    assert response.status_code == 404


def test_update_department(client, make_department):
    dept = make_department(code="DEPT-UPDATE")
    response = client.put(f"/departments/{dept['id']}", json={"name": "Renamed Dept"})
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed Dept"


def test_delete_department(client, make_department):
    dept = make_department(code="DEPT-DELETE")
    response = client.delete(f"/departments/{dept['id']}")
    assert response.status_code == 200
    follow_up = client.get(f"/departments/{dept['id']}")
    assert follow_up.status_code == 404
