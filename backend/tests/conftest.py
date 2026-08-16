import os
import sys

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import Base  # noqa: E402
from app.main import app  # noqa: E402

from app.models import organization  # noqa: F401,E402
from app.models import department  # noqa: F401,E402
from app.models import role  # noqa: F401,E402
from app.models import qualification  # noqa: F401,E402
from app.models import employee  # noqa: F401,E402
from app.models import employee_qualification  # noqa: F401,E402
from app.models import demand_task  # noqa: F401,E402
from app.models import shift  # noqa: F401,E402
from app.models import employee_shift  # noqa: F401,E402

from app.routers import organizations as organizations_router  # noqa: E402
from app.routers import departments as departments_router  # noqa: E402
from app.routers import roles as roles_router  # noqa: E402
from app.routers import employees as employees_router  # noqa: E402
from app.routers import qualifications as qualifications_router  # noqa: E402
from app.routers import employee_qualifications as employee_qualifications_router  # noqa: E402
from app.routers import demand_tasks as demand_tasks_router  # noqa: E402
from app.routers import demand_calculator as demand_calculator_router  # noqa: E402
from app.routers import workforce_coverage as workforce_coverage_router  # noqa: E402


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL environment variable is required to run the "
        "test suite and was not set. This must point to a dedicated "
        "PostgreSQL test database, SEPARATE from the development database "
        "(cedar-db). Do NOT reuse DATABASE_URL for this. Example: "
        "postgresql+psycopg2://cedar:cedar@127.0.0.1:5434/cedar_test"
    )


_ROUTER_MODULES_WITH_GET_DB = [
    organizations_router,
    departments_router,
    roles_router,
    employees_router,
    qualifications_router,
    employee_qualifications_router,
    demand_tasks_router,
    demand_calculator_router,
    workforce_coverage_router,
]


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()

    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = testing_session_local()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    for module in _ROUTER_MODULES_WITH_GET_DB:
        app.dependency_overrides[module.get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def make_organization(client):
    def _make(code="ORG-1", name="Test Organization"):
        response = client.post("/organizations", json={"name": name, "code": code})
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture()
def make_department(client, make_organization):
    def _make(organization_id=None, code="DEPT-1", name="Test Department"):
        if organization_id is None:
            organization_id = make_organization()["id"]
        response = client.post(
            "/departments",
            json={"organization_id": organization_id, "name": name, "code": code},
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture()
def make_role(client, make_organization):
    def _make(organization_id=None, code="ROLE-1", name="Test Role"):
        if organization_id is None:
            organization_id = make_organization()["id"]
        response = client.post(
            "/roles",
            json={"organization_id": organization_id, "name": name, "code": code},
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture()
def make_employee(client, make_organization, make_department, make_role):
    def _make(
        employee_number="EMP-1",
        email=None,
        organization_id=None,
        department_id=None,
        role_id=None,
    ):
        if organization_id is None:
            organization_id = make_organization()["id"]
        if department_id is None:
            department_id = make_department(organization_id=organization_id)["id"]
        if role_id is None:
            role_id = make_role(organization_id=organization_id)["id"]

        response = client.post(
            "/employees",
            json={
                "organization_id": organization_id,
                "department_id": department_id,
                "role_id": role_id,
                "employee_number": employee_number,
                "first_name": "Ana",
                "last_name": "Pop",
                "email": email or f"{employee_number.lower()}@example.com",
                "employment_type": "FULL_TIME",
                "hire_date": "2026-01-01",
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture()
def make_demand_task(client, make_organization):
    def _make(
        organization_id=None,
        flight_reference="FL-100",
        task_type="TURNAROUND",
        start_time="2026-01-01T08:00:00Z",
        duration_minutes=60,
        target_headcount=10,
        minimum_headcount=8,
    ):
        if organization_id is None:
            organization_id = make_organization()["id"]

        response = client.post(
            "/demand-tasks",
            json={
                "organization_id": organization_id,
                "flight_reference": flight_reference,
                "task_type": task_type,
                "start_time": start_time,
                "duration_minutes": duration_minutes,
                "target_headcount": target_headcount,
                "minimum_headcount": minimum_headcount,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _make