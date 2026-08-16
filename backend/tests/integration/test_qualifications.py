def test_create_qualification(client, make_organization):
    org = make_organization(code="ORG-QUAL-1")
    response = client.post(
        "/qualifications",
        json={
            "organization_id": org["id"],
            "name": "Forklift Operator",
            "code": "QUAL-FORKLIFT",
            "requires_expiration": False,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["code"] == "QUAL-FORKLIFT"
    assert body["requires_expiration"] is False
    assert body["default_validity_months"] is None


def test_create_qualification_requires_expiration_without_validity_rejected(client, make_organization):
    org = make_organization(code="ORG-QUAL-2")
    response = client.post(
        "/qualifications",
        json={
            "organization_id": org["id"],
            "name": "Hazmat Handling",
            "code": "QUAL-HAZMAT",
            "requires_expiration": True,
        },
    )
    assert response.status_code == 422


def test_create_qualification_validity_without_requires_expiration_rejected(client, make_organization):
    org = make_organization(code="ORG-QUAL-3")
    response = client.post(
        "/qualifications",
        json={
            "organization_id": org["id"],
            "name": "Basic Safety",
            "code": "QUAL-SAFETY",
            "requires_expiration": False,
            "default_validity_months": 12,
        },
    )
    assert response.status_code == 422


def test_create_qualification_invalid_organization_rejected(client):
    response = client.post(
        "/qualifications",
        json={
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "name": "Ghost Qualification",
            "code": "QUAL-GHOST",
            "requires_expiration": False,
        },
    )
    assert response.status_code == 400


def test_create_qualification_duplicate_code_rejected(client, make_organization):
    org = make_organization(code="ORG-QUAL-4")
    payload = {
        "organization_id": org["id"],
        "name": "Duplicate Qual",
        "code": "QUAL-DUP",
        "requires_expiration": False,
    }
    first = client.post("/qualifications", json=payload)
    assert first.status_code == 201

    second = client.post("/qualifications", json=dict(payload, name="Another name"))
    assert second.status_code == 400


def test_get_qualification_not_found(client):
    response = client.get("/qualifications/11111111-1111-1111-1111-111111111111")
    assert response.status_code == 404


def test_update_qualification_expiration_rule_enforced(client, make_organization):
    org = make_organization(code="ORG-QUAL-5")
    created = client.post(
        "/qualifications",
        json={
            "organization_id": org["id"],
            "name": "Update Rule Qual",
            "code": "QUAL-UPDATE-RULE",
            "requires_expiration": False,
        },
    ).json()

    response = client.put(
        f"/qualifications/{created['id']}",
        json={"requires_expiration": True},
    )
    # Milestone 4C: normalized to 422, consistent with the same rule at create.
    assert response.status_code == 422


def test_update_qualification_expiration_rule_enforced_other_direction(client, make_organization):
    org = make_organization(code="ORG-QUAL-7")
    created = client.post(
        "/qualifications",
        json={
            "organization_id": org["id"],
            "name": "Update Rule Qual Other Direction",
            "code": "QUAL-UPDATE-RULE-2",
            "requires_expiration": True,
            "default_validity_months": 12,
        },
    ).json()

    response = client.put(
        f"/qualifications/{created['id']}",
        json={"requires_expiration": False},
    )
    assert response.status_code == 422


def test_delete_qualification(client, make_organization):
    org = make_organization(code="ORG-QUAL-6")
    created = client.post(
        "/qualifications",
        json={
            "organization_id": org["id"],
            "name": "Delete Qual",
            "code": "QUAL-DELETE",
            "requires_expiration": False,
        },
    ).json()

    response = client.delete(f"/qualifications/{created['id']}")
    assert response.status_code == 200
    follow_up = client.get(f"/qualifications/{created['id']}")
    assert follow_up.status_code == 404