def test_create_organization(client):
    response = client.post(
        "/organizations",
        json={"name": "Acme Ground Handling", "code": "ACME"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Acme Ground Handling"
    assert body["code"] == "ACME"
    assert body["is_active"] is True
    assert "id" in body


def test_get_organization(client, make_organization):
    created = make_organization(code="ORG-GET")
    response = client.get(f"/organizations/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_organization_not_found(client):
    response = client.get("/organizations/11111111-1111-1111-1111-111111111111")
    assert response.status_code == 404


def test_list_organizations(client, make_organization):
    make_organization(code="ORG-LIST-1")
    make_organization(code="ORG-LIST-2")
    response = client.get("/organizations")
    assert response.status_code == 200
    codes = {item["code"] for item in response.json()}
    assert {"ORG-LIST-1", "ORG-LIST-2"}.issubset(codes)


def test_create_organization_duplicate_code_rejected(client, make_organization):
    make_organization(code="DUPLICATE-ORG")
    response = client.post(
        "/organizations",
        json={"name": "Another Org", "code": "DUPLICATE-ORG"},
    )
    assert response.status_code == 400


def test_update_organization(client, make_organization):
    created = make_organization(code="ORG-UPDATE")
    response = client.put(f"/organizations/{created['id']}", json={"name": "Renamed Org"})
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed Org"


def test_delete_organization(client, make_organization):
    created = make_organization(code="ORG-DELETE")
    response = client.delete(f"/organizations/{created['id']}")
    assert response.status_code == 200

    follow_up = client.get(f"/organizations/{created['id']}")
    assert follow_up.status_code == 404
