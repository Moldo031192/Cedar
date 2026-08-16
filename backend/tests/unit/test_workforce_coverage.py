import uuid
from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.demand_task import DemandTask, DemandTaskType, DemandTaskStatus
from app.models.employee import Employee, EmploymentType
from app.models.employee_qualification import (
    EmployeeQualification,
    EmployeeQualificationStatus,
)
from app.models.qualification import Qualification
from app.schemas.workforce_coverage import WorkforceCoverageRequest
from app.services.workforce_coverage import calculate_workforce_coverage


def _make_qualification(name="FORKLIFT"):
    return Qualification(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        name=name,
        code=name,
        requires_expiration=False,
        is_active=True,
    )


def _make_employee(employee_number="EMP-1", qualifications=None):
    employee = Employee(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        department_id=uuid.uuid4(),
        role_id=uuid.uuid4(),
        employee_number=employee_number,
        first_name="Ana",
        last_name="Pop",
        email=f"{employee_number.lower()}@example.com",
        employment_type=EmploymentType.FULL_TIME,
        hire_date=date(2026, 1, 1),
        is_active=True,
    )
    employee.employee_qualifications = [
        EmployeeQualification(
            employee_id=employee.id,
            qualification_id=qualification.id,
            obtained_at=date(2026, 1, 1),
            status=EmployeeQualificationStatus.ACTIVE,
        )
        for qualification in (qualifications or [])
    ]
    return employee


def _make_task(start_time, duration_minutes, required_qualifications=None, status=DemandTaskStatus.PLANNED):
    task = DemandTask(
        organization_id=uuid.uuid4(),
        flight_reference="TEST123",
        task_type=DemandTaskType.TURNAROUND,
        start_time=start_time,
        duration_minutes=duration_minutes,
        target_headcount=10,
        minimum_headcount=8,
        status=status,
    )
    task.required_qualifications = required_qualifications or []
    return task


def test_no_employees_returns_empty_eligible_list():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    intervals, eligible = calculate_workforce_coverage(
        tasks=[],
        employees=[],
        window_start=window_start,
        window_end=window_end,
        available_headcount=14,
    )

    assert eligible == []
    assert len(intervals) == 1
    assert intervals[0]["status"] == "COVERED"


def test_employee_eligible_when_task_has_no_required_qualifications():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    task = _make_task(start_time=window_start, duration_minutes=60, required_qualifications=[])
    employee = _make_employee(qualifications=[])

    intervals, eligible = calculate_workforce_coverage(
        tasks=[task],
        employees=[employee],
        window_start=window_start,
        window_end=window_end,
        available_headcount=14,
    )

    assert len(eligible) == 1
    assert eligible[0]["eligible"] is True
    assert eligible[0]["missing_qualification_ids"] == []


def test_employee_ineligible_when_missing_required_qualification():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    forklift = _make_qualification("FORKLIFT")
    task = _make_task(start_time=window_start, duration_minutes=60, required_qualifications=[forklift])
    employee = _make_employee(qualifications=[])

    intervals, eligible = calculate_workforce_coverage(
        tasks=[task],
        employees=[employee],
        window_start=window_start,
        window_end=window_end,
        available_headcount=14,
    )

    assert len(eligible) == 1
    assert eligible[0]["eligible"] is False
    assert eligible[0]["missing_qualification_ids"] == [forklift.id]


def test_employee_eligible_when_holding_required_qualification():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    forklift = _make_qualification("FORKLIFT")
    task = _make_task(start_time=window_start, duration_minutes=60, required_qualifications=[forklift])
    employee = _make_employee(qualifications=[forklift])

    intervals, eligible = calculate_workforce_coverage(
        tasks=[task],
        employees=[employee],
        window_start=window_start,
        window_end=window_end,
        available_headcount=14,
    )

    assert eligible[0]["eligible"] is True
    assert eligible[0]["missing_qualification_ids"] == []


def test_multiple_employees_mixed_eligibility():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    forklift = _make_qualification("FORKLIFT")
    task = _make_task(start_time=window_start, duration_minutes=60, required_qualifications=[forklift])

    qualified_employee = _make_employee("EMP-1", qualifications=[forklift])
    unqualified_employee = _make_employee("EMP-2", qualifications=[])

    intervals, eligible = calculate_workforce_coverage(
        tasks=[task],
        employees=[qualified_employee, unqualified_employee],
        window_start=window_start,
        window_end=window_end,
        available_headcount=14,
    )

    results = {item["employee_number"]: item["eligible"] for item in eligible}
    assert results["EMP-1"] is True
    assert results["EMP-2"] is False


def test_zero_eligible_employees_when_none_hold_required_qualification():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    forklift = _make_qualification("FORKLIFT")
    task = _make_task(start_time=window_start, duration_minutes=60, required_qualifications=[forklift])

    employees = [_make_employee("EMP-1"), _make_employee("EMP-2")]

    intervals, eligible = calculate_workforce_coverage(
        tasks=[task],
        employees=employees,
        window_start=window_start,
        window_end=window_end,
        available_headcount=14,
    )

    assert all(item["eligible"] is False for item in eligible)


def test_end_time_must_be_after_start_time():
    with pytest.raises(ValidationError):
        WorkforceCoverageRequest(
            organization_id=uuid.uuid4(),
            start_time=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc),
        )
