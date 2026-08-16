def test_create_role(client, make_organization):
    org = make_organization(code="ORG-ROLE-1")
    response = client.post(
        "/roles",
        json={"organization_id": org["id"], "name": "Ramp Agent", "code": "ROLE-RAMP"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["code"] == "ROLE-RAMP"


def test_create_role_invalid_organization_rejected(client):
    response = client.post(
        "/roles",
        json={
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "name": "Ghost Role",
            "code": "ROLE-GHOST",
        },
    )
    assert response.status_code == 400


def test_create_role_duplicate_code_rejected(client, make_organization, make_role):
    org = make_organization(code="ORG-ROLE-2")
    make_role(organization_id=org["id"], code="ROLE-DUP")
    response = client.post(
        "/roles",
        json={"organization_id": org["id"], "name": "Second Role", "code": "ROLE-DUP"},
    )
    assert response.status_code == 400


def test_get_role_not_found(client):
    response = client.get("/roles/11111111-1111-1111-1111-111111111111")
    assert response.status_code == 404


def test_update_role(client, make_role):
    role = make_role(code="ROLE-UPDATE")
    response = client.put(f"/roles/{role['id']}", json={"name": "Renamed Role"})
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed Role"


def test_delete_role(client, make_role):
    role = make_role(code="ROLE-DELETE")
    response = client.delete(f"/roles/{role['id']}")
    assert response.status_code == 200
    follow_up = client.get(f"/roles/{role['id']}")
    assert follow_up.status_code == 404
