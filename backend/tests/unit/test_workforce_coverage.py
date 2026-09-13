import uuid
from datetime import date, datetime, time, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.models.demand_task import DemandTask, DemandTaskType, DemandTaskStatus
from app.models.employee import Employee, EmploymentType
from app.models.employee_qualification import (
    EmployeeQualification,
    EmployeeQualificationStatus,
)
from app.models.employee_shift import EmployeeShift
from app.models.qualification import Qualification
from app.models.shift import Shift
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


def _make_employee(employee_number="EMP-1", qualifications=None, is_active=True):
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
        is_active=is_active,
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


def _make_employee_with_qualification_status(
    qualification,
    status,
    expires_at=None,
    employee_number="EMP-1",
):
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
            expires_at=expires_at,
            status=status,
        )
    ]
    return employee


def _make_shift(
    start_time=time(6, 0),
    end_time=time(14, 0),
    crosses_midnight=False,
    is_active=True,
):
    return Shift(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        name="Test Shift",
        code="SHIFT-1",
        start_time=start_time,
        end_time=end_time,
        crosses_midnight=crosses_midnight,
        is_active=is_active,
    )


def _make_employee_shift(employee, shift, work_date, is_present=True):
    employee_shift = EmployeeShift(
        id=uuid.uuid4(),
        employee_id=employee.id,
        shift_id=shift.id,
        work_date=work_date,
        is_present=is_present,
    )
    employee_shift.employee = employee
    employee_shift.shift = shift
    return employee_shift


def _make_task(start_time, duration_minutes, required_qualifications=None, status=DemandTaskStatus.PLANNED):
    task = DemandTask(
        id=uuid.uuid4(),
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


# --- Basic workforce / no-data cases ---


def test_no_employee_shifts_returns_zero_workforce():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    intervals, task_eligibility = calculate_workforce_coverage(
        tasks=[],
        employee_shifts=[],
        window_start=window_start,
        window_end=window_end,
    )

    assert len(intervals) == 1
    assert intervals[0]["scheduled_workforce"] == 0
    assert intervals[0]["status"] == "COVERED"
    assert task_eligibility == []


def test_active_present_overlapping_employee_shift_counts():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    employee = _make_employee("EMP-1")
    shift = _make_shift(start_time=time(6, 0), end_time=time(14, 0))
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1))

    intervals, _ = calculate_workforce_coverage(
        tasks=[],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    assert intervals[0]["scheduled_workforce"] == 1


def test_absent_employee_shift_does_not_count():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    employee = _make_employee("EMP-1")
    shift = _make_shift(start_time=time(6, 0), end_time=time(14, 0))
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1), is_present=False)

    intervals, _ = calculate_workforce_coverage(
        tasks=[],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    assert intervals[0]["scheduled_workforce"] == 0


def test_inactive_employee_does_not_count():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    employee = _make_employee("EMP-1", is_active=False)
    shift = _make_shift(start_time=time(6, 0), end_time=time(14, 0))
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1))

    intervals, _ = calculate_workforce_coverage(
        tasks=[],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    assert intervals[0]["scheduled_workforce"] == 0


def test_inactive_shift_does_not_count():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    employee = _make_employee("EMP-1")
    shift = _make_shift(start_time=time(6, 0), end_time=time(14, 0), is_active=False)
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1))

    intervals, _ = calculate_workforce_coverage(
        tasks=[],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    assert intervals[0]["scheduled_workforce"] == 0


def test_non_overlapping_shift_does_not_count():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    employee = _make_employee("EMP-1")
    shift = _make_shift(start_time=time(16, 0), end_time=time(22, 0))
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1))

    intervals, _ = calculate_workforce_coverage(
        tasks=[],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    assert intervals[0]["scheduled_workforce"] == 0


def test_partially_overlapping_shift_counted_only_during_overlap():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    employee = _make_employee("EMP-1")
    shift = _make_shift(start_time=time(6, 0), end_time=time(10, 0))
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1))

    intervals, _ = calculate_workforce_coverage(
        tasks=[],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    before = [i for i in intervals if i["start_time"] == window_start][0]
    after = [i for i in intervals if i["end_time"] == window_end][0]

    assert before["scheduled_workforce"] == 1
    assert after["scheduled_workforce"] == 0


def test_multiple_shifts_produce_correct_interval_specific_workforce():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    employee_a = _make_employee("EMP-A")
    employee_b = _make_employee("EMP-B")

    shift_a = _make_shift(start_time=time(6, 0), end_time=time(10, 0))
    shift_b = _make_shift(start_time=time(9, 0), end_time=time(13, 0))

    employee_shift_a = _make_employee_shift(employee_a, shift_a, date(2026, 1, 1))
    employee_shift_b = _make_employee_shift(employee_b, shift_b, date(2026, 1, 1))

    intervals, _ = calculate_workforce_coverage(
        tasks=[],
        employee_shifts=[employee_shift_a, employee_shift_b],
        window_start=window_start,
        window_end=window_end,
    )

    overlap = [
        i
        for i in intervals
        if i["start_time"] == datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
        and i["end_time"] == datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    ]
    assert len(overlap) == 1
    assert overlap[0]["scheduled_workforce"] == 2


def test_scheduled_workforce_counts_distinct_employees_not_shift_rows():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    employee = _make_employee("EMP-1")
    shift_a = _make_shift(start_time=time(6, 0), end_time=time(14, 0))
    shift_b = _make_shift(start_time=time(7, 0), end_time=time(15, 0))

    employee_shift_a = _make_employee_shift(employee, shift_a, date(2026, 1, 1))
    employee_shift_b = _make_employee_shift(employee, shift_b, date(2026, 1, 1))

    intervals, _ = calculate_workforce_coverage(
        tasks=[],
        employee_shifts=[employee_shift_a, employee_shift_b],
        window_start=window_start,
        window_end=window_end,
    )

    assert intervals[0]["scheduled_workforce"] == 1


# --- Midnight-crossing shifts ---


def test_normal_shift_datetime_range():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    employee = _make_employee("EMP-1")
    shift = _make_shift(start_time=time(6, 0), end_time=time(14, 0), crosses_midnight=False)
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1))

    intervals, _ = calculate_workforce_coverage(
        tasks=[],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    assert intervals[0]["scheduled_workforce"] == 1


def test_midnight_crossing_shift_coverage_before_midnight():
    window_start = datetime(2026, 1, 1, 23, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 2, 1, 0, tzinfo=timezone.utc)

    employee = _make_employee("EMP-1")
    shift = _make_shift(start_time=time(22, 0), end_time=time(6, 0), crosses_midnight=True)
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1))

    intervals, _ = calculate_workforce_coverage(
        tasks=[],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    assert intervals[0]["scheduled_workforce"] == 1


def test_midnight_crossing_shift_coverage_after_midnight():
    window_start = datetime(2026, 1, 2, 2, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 2, 4, 0, tzinfo=timezone.utc)

    employee = _make_employee("EMP-1")
    shift = _make_shift(start_time=time(22, 0), end_time=time(6, 0), crosses_midnight=True)
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1))

    intervals, _ = calculate_workforce_coverage(
        tasks=[],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    assert intervals[0]["scheduled_workforce"] == 1


def test_midnight_crossing_shift_coverage_interval_crosses_midnight():
    window_start = datetime(2026, 1, 1, 21, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 2, 7, 0, tzinfo=timezone.utc)

    employee = _make_employee("EMP-1")
    shift = _make_shift(start_time=time(22, 0), end_time=time(6, 0), crosses_midnight=True)
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1))

    intervals, _ = calculate_workforce_coverage(
        tasks=[],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    during = [
        i
        for i in intervals
        if i["start_time"] == datetime(2026, 1, 1, 22, 0, tzinfo=timezone.utc)
        and i["end_time"] == datetime(2026, 1, 2, 6, 0, tzinfo=timezone.utc)
    ]
    assert len(during) == 1
    assert during[0]["scheduled_workforce"] == 1

    before = [i for i in intervals if i["start_time"] == window_start][0]
    after = [i for i in intervals if i["end_time"] == window_end][0]
    assert before["scheduled_workforce"] == 0
    assert after["scheduled_workforce"] == 0


# --- Task-level qualification eligibility ---


def test_task_eligibility_valid_required_qualification():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    forklift = _make_qualification("FORKLIFT")
    employee = _make_employee("EMP-1", qualifications=[forklift])
    shift = _make_shift(start_time=time(6, 0), end_time=time(14, 0))
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1))

    task = _make_task(start_time=window_start, duration_minutes=60, required_qualifications=[forklift])

    _, task_eligibility = calculate_workforce_coverage(
        tasks=[task],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    assert len(task_eligibility) == 1
    assert task_eligibility[0]["employees"][0]["eligible"] is True
    assert task_eligibility[0]["employees"][0]["missing_qualification_ids"] == []


def test_task_eligibility_missing_qualification():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    forklift = _make_qualification("FORKLIFT")
    employee = _make_employee("EMP-1", qualifications=[])
    shift = _make_shift(start_time=time(6, 0), end_time=time(14, 0))
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1))

    task = _make_task(start_time=window_start, duration_minutes=60, required_qualifications=[forklift])

    _, task_eligibility = calculate_workforce_coverage(
        tasks=[task],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    employee_result = task_eligibility[0]["employees"][0]
    assert employee_result["eligible"] is False
    assert employee_result["missing_qualification_ids"] == [forklift.id]


def test_task_eligibility_expired_status_ineligible():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    forklift = _make_qualification("FORKLIFT")
    employee = _make_employee_with_qualification_status(
        forklift, status=EmployeeQualificationStatus.EXPIRED, expires_at=None
    )
    shift = _make_shift(start_time=time(6, 0), end_time=time(14, 0))
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1))

    task = _make_task(start_time=window_start, duration_minutes=60, required_qualifications=[forklift])

    _, task_eligibility = calculate_workforce_coverage(
        tasks=[task],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    assert task_eligibility[0]["employees"][0]["eligible"] is False


def test_task_eligibility_suspended_status_ineligible():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    forklift = _make_qualification("FORKLIFT")
    employee = _make_employee_with_qualification_status(
        forklift, status=EmployeeQualificationStatus.SUSPENDED, expires_at=None
    )
    shift = _make_shift(start_time=time(6, 0), end_time=time(14, 0))
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1))

    task = _make_task(start_time=window_start, duration_minutes=60, required_qualifications=[forklift])

    _, task_eligibility = calculate_workforce_coverage(
        tasks=[task],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    assert task_eligibility[0]["employees"][0]["eligible"] is False


def test_task_eligibility_expired_by_date_ineligible():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    forklift = _make_qualification("FORKLIFT")
    employee = _make_employee_with_qualification_status(
        forklift,
        status=EmployeeQualificationStatus.ACTIVE,
        expires_at=date.today() - timedelta(days=1),
    )
    shift = _make_shift(start_time=time(6, 0), end_time=time(14, 0))
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1))

    task = _make_task(start_time=window_start, duration_minutes=60, required_qualifications=[forklift])

    _, task_eligibility = calculate_workforce_coverage(
        tasks=[task],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    employee_result = task_eligibility[0]["employees"][0]
    assert employee_result["eligible"] is False
    assert employee_result["missing_qualification_ids"] == [forklift.id]


def test_task_eligibility_expires_today_remains_valid():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    forklift = _make_qualification("FORKLIFT")
    employee = _make_employee_with_qualification_status(
        forklift, status=EmployeeQualificationStatus.ACTIVE, expires_at=date.today()
    )
    shift = _make_shift(start_time=time(6, 0), end_time=time(14, 0))
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1))

    task = _make_task(start_time=window_start, duration_minutes=60, required_qualifications=[forklift])

    _, task_eligibility = calculate_workforce_coverage(
        tasks=[task],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    assert task_eligibility[0]["employees"][0]["eligible"] is True


def test_employee_eligible_for_task_a_but_not_task_b():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    gpu = _make_qualification("GPU")
    stairs = _make_qualification("STAIRS")

    employee = _make_employee("EMP-1", qualifications=[gpu])
    shift = _make_shift(start_time=time(6, 0), end_time=time(14, 0))
    employee_shift = _make_employee_shift(employee, shift, date(2026, 1, 1))

    task_a = _make_task(
        start_time=datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc),
        duration_minutes=60,
        required_qualifications=[gpu],
    )
    task_b = _make_task(
        start_time=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        duration_minutes=60,
        required_qualifications=[stairs],
    )

    _, task_eligibility = calculate_workforce_coverage(
        tasks=[task_a, task_b],
        employee_shifts=[employee_shift],
        window_start=window_start,
        window_end=window_end,
    )

    results = {item["task_id"]: item["employees"][0]["eligible"] for item in task_eligibility}
    assert results[task_a.id] is True
    assert results[task_b.id] is False


def test_employee_without_overlapping_shift_not_listed_for_task():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    task = _make_task(start_time=window_start, duration_minutes=60, required_qualifications=[])

    _, task_eligibility = calculate_workforce_coverage(
        tasks=[task],
        employee_shifts=[],
        window_start=window_start,
        window_end=window_end,
    )

    assert task_eligibility[0]["employees"] == []


# --- Coverage status thresholds ---


def test_coverage_status_covered():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)

    employees_shifts = []
    for i in range(10):
        employee = _make_employee(f"EMP-{i}")
        shift = _make_shift(start_time=time(6, 0), end_time=time(14, 0))
        employees_shifts.append(_make_employee_shift(employee, shift, date(2026, 1, 1)))

    task = _make_task(start_time=window_start, duration_minutes=60, required_qualifications=[])
    task.target_headcount = 10
    task.minimum_headcount = 8

    intervals, _ = calculate_workforce_coverage(
        tasks=[task],
        employee_shifts=employees_shifts,
        window_start=window_start,
        window_end=window_end,
    )

    assert intervals[0]["status"] == "COVERED"


def test_coverage_status_target_not_covered():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)

    employees_shifts = []
    for i in range(8):
        employee = _make_employee(f"EMP-{i}")
        shift = _make_shift(start_time=time(6, 0), end_time=time(14, 0))
        employees_shifts.append(_make_employee_shift(employee, shift, date(2026, 1, 1)))

    task = _make_task(start_time=window_start, duration_minutes=60, required_qualifications=[])
    task.target_headcount = 10
    task.minimum_headcount = 8

    intervals, _ = calculate_workforce_coverage(
        tasks=[task],
        employee_shifts=employees_shifts,
        window_start=window_start,
        window_end=window_end,
    )

    assert intervals[0]["status"] == "TARGET_NOT_COVERED"


def test_coverage_status_minimum_not_covered():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)

    employees_shifts = []
    for i in range(3):
        employee = _make_employee(f"EMP-{i}")
        shift = _make_shift(start_time=time(6, 0), end_time=time(14, 0))
        employees_shifts.append(_make_employee_shift(employee, shift, date(2026, 1, 1)))

    task = _make_task(start_time=window_start, duration_minutes=60, required_qualifications=[])
    task.target_headcount = 10
    task.minimum_headcount = 8

    intervals, _ = calculate_workforce_coverage(
        tasks=[task],
        employee_shifts=employees_shifts,
        window_start=window_start,
        window_end=window_end,
    )

    assert intervals[0]["status"] == "MINIMUM_NOT_COVERED"


def test_overlapping_tasks_aggregate_demand_correctly():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    task_a = _make_task(start_time=window_start, duration_minutes=60, required_qualifications=[])
    task_a.target_headcount = 6
    task_a.minimum_headcount = 4

    task_b = _make_task(
        start_time=datetime(2026, 1, 1, 8, 30, tzinfo=timezone.utc),
        duration_minutes=60,
        required_qualifications=[],
    )
    task_b.target_headcount = 5
    task_b.minimum_headcount = 3

    intervals, _ = calculate_workforce_coverage(
        tasks=[task_a, task_b],
        employee_shifts=[],
        window_start=window_start,
        window_end=window_end,
    )

    overlap = [
        i
        for i in intervals
        if i["start_time"] == datetime(2026, 1, 1, 8, 30, tzinfo=timezone.utc)
        and i["end_time"] == datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
    ]
    assert len(overlap) == 1
    assert overlap[0]["target_demand"] == 11
    assert overlap[0]["minimum_demand"] == 7


def test_end_time_must_be_after_start_time():
    with pytest.raises(ValidationError):
        WorkforceCoverageRequest(
            organization_id=uuid.uuid4(),
            start_time=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc),
        )