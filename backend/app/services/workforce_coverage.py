from datetime import date, datetime, timedelta, timezone
from typing import Iterable

from app.models.demand_task import DemandTask
from app.models.employee_shift import EmployeeShift
from app.models.employee_qualification import EmployeeQualificationStatus


def _shift_datetime_range(employee_shift: EmployeeShift) -> tuple[datetime, datetime]:
    """
    Construct the absolute [start, end) datetime range a shift assignment
    covers, given its work_date and the parent Shift's start_time/end_time/
    crosses_midnight. work_date is the calendar date the shift STARTS on
    (Milestone 6/7 semantics). Shift local times are treated as UTC,
    consistent with the rest of Cedar, which does not otherwise model
    timezones.
    """
    shift = employee_shift.shift
    work_date = employee_shift.work_date

    start_dt = datetime.combine(work_date, shift.start_time, tzinfo=timezone.utc)

    if shift.crosses_midnight:
        end_date = work_date + timedelta(days=1)
    else:
        end_date = work_date

    end_dt = datetime.combine(end_date, shift.end_time, tzinfo=timezone.utc)

    return start_dt, end_dt


def _is_active_assignment(employee_shift: EmployeeShift) -> bool:
    return (
        employee_shift.is_present
        and employee_shift.employee.is_active
        and employee_shift.shift.is_active
    )


def _is_qualification_valid(employee_qualification, today: date) -> bool:
    return employee_qualification.status == EmployeeQualificationStatus.ACTIVE and (
        employee_qualification.expires_at is None
        or employee_qualification.expires_at >= today
    )


def calculate_workforce_coverage(
    tasks: Iterable[DemandTask],
    employee_shifts: Iterable[EmployeeShift],
    window_start: datetime,
    window_end: datetime,
) -> tuple[list[dict], list[dict]]:
    """
    Calculate workforce coverage against demand, derived from actual
    EmployeeShift assignments (Milestone 7).

    Workforce is no longer a caller-supplied number. An EmployeeShift
    contributes to workforce only when:
      - the employee is active
      - EmployeeShift.is_present is true
      - the shift itself is active
      - the shift's absolute time range overlaps the relevant interval

    scheduled_workforce counts DISTINCT employees per interval - an
    employee is never counted twice regardless of overlapping tasks or
    query joins.

    Qualification eligibility (Milestone 4B rule, unchanged): an
    EmployeeQualification only counts if status == ACTIVE and expires_at
    is either null or not in the past, evaluated against date.today().

    Task eligibility answers "does this employee hold the required
    qualifications for this task", evaluated only for employees whose
    shift overlaps that task's own time range (clamped to the requested
    window). It does NOT mean the employee has been assigned to execute
    the task - assignment/optimization is out of scope for M7.
    """

    tasks = list(tasks)
    today = date.today()

    active_tasks = [
        task
        for task in tasks
        if task.start_time < window_end
        and task.end_time > window_start
        and task.status.value != "CANCELLED"
    ]

    active_assignments = [
        employee_shift
        for employee_shift in employee_shifts
        if _is_active_assignment(employee_shift)
    ]

    assignment_ranges = [
        (employee_shift,) + _shift_datetime_range(employee_shift)
        for employee_shift in active_assignments
    ]

    assignment_ranges = [
        (employee_shift, start, end)
        for employee_shift, start, end in assignment_ranges
        if start < window_end and end > window_start
    ]

    intervals = _calculate_intervals(
        active_tasks=active_tasks,
        assignment_ranges=assignment_ranges,
        window_start=window_start,
        window_end=window_end,
    )

    task_eligibility = _calculate_task_eligibility(
        active_tasks=active_tasks,
        assignment_ranges=assignment_ranges,
        window_start=window_start,
        window_end=window_end,
        today=today,
    )

    return intervals, task_eligibility


def _calculate_intervals(
    active_tasks: list[DemandTask],
    assignment_ranges: list[tuple[EmployeeShift, datetime, datetime]],
    window_start: datetime,
    window_end: datetime,
) -> list[dict]:

    time_points = {window_start, window_end}

    for task in active_tasks:
        time_points.add(max(task.start_time, window_start))
        time_points.add(min(task.end_time, window_end))

    for _, start, end in assignment_ranges:
        time_points.add(max(start, window_start))
        time_points.add(min(end, window_end))

    sorted_points = sorted(time_points)

    intervals = []

    for index in range(len(sorted_points) - 1):
        interval_start = sorted_points[index]
        interval_end = sorted_points[index + 1]

        if interval_start >= interval_end:
            continue

        overlapping_tasks = [
            task
            for task in active_tasks
            if task.start_time < interval_end and task.end_time > interval_start
        ]

        target_demand = sum(task.target_headcount for task in overlapping_tasks)
        minimum_demand = sum(task.minimum_headcount for task in overlapping_tasks)

        overlapping_employee_ids = {
            employee_shift.employee_id
            for employee_shift, start, end in assignment_ranges
            if start < interval_end and end > interval_start
        }
        scheduled_workforce = len(overlapping_employee_ids)

        intervals.append(
            _build_interval(
                start_time=interval_start,
                end_time=interval_end,
                target_demand=target_demand,
                minimum_demand=minimum_demand,
                scheduled_workforce=scheduled_workforce,
            )
        )

    return intervals


def _build_interval(
    start_time: datetime,
    end_time: datetime,
    target_demand: int,
    minimum_demand: int,
    scheduled_workforce: int,
) -> dict:

    target_gap = max(0, target_demand - scheduled_workforce)
    minimum_gap = max(0, minimum_demand - scheduled_workforce)

    if target_demand <= scheduled_workforce:
        status = "COVERED"
    elif minimum_demand <= scheduled_workforce:
        status = "TARGET_NOT_COVERED"
    else:
        status = "MINIMUM_NOT_COVERED"

    return {
        "start_time": start_time,
        "end_time": end_time,
        "target_demand": target_demand,
        "minimum_demand": minimum_demand,
        "scheduled_workforce": scheduled_workforce,
        "target_gap": target_gap,
        "minimum_gap": minimum_gap,
        "status": status,
    }


def _calculate_task_eligibility(
    active_tasks: list[DemandTask],
    assignment_ranges: list[tuple[EmployeeShift, datetime, datetime]],
    window_start: datetime,
    window_end: datetime,
    today: date,
) -> list[dict]:

    task_eligibility = []

    for task in active_tasks:
        task_effective_start = max(task.start_time, window_start)
        task_effective_end = min(task.end_time, window_end)

        required_qualification_ids = {
            qualification.id for qualification in task.required_qualifications
        }

        seen_employee_ids = set()
        employees_payload = []

        for employee_shift, start, end in assignment_ranges:
            if start >= task_effective_end or end <= task_effective_start:
                continue

            employee = employee_shift.employee

            if employee.id in seen_employee_ids:
                continue
            seen_employee_ids.add(employee.id)

            held_qualification_ids = {
                eq.qualification_id
                for eq in employee.employee_qualifications
                if _is_qualification_valid(eq, today)
            }

            missing_qualification_ids = required_qualification_ids - held_qualification_ids

            employees_payload.append(
                {
                    "employee_id": employee.id,
                    "employee_number": employee.employee_number,
                    "employee_name": f"{employee.first_name} {employee.last_name}",
                    "eligible": len(missing_qualification_ids) == 0,
                    "missing_qualification_ids": list(missing_qualification_ids),
                }
            )

        employees_payload.sort(key=lambda item: item["employee_number"])

        task_eligibility.append(
            {
                "task_id": task.id,
                "flight_reference": task.flight_reference,
                "start_time": task.start_time,
                "end_time": task.end_time,
                "employees": employees_payload,
            }
        )

    return task_eligibility