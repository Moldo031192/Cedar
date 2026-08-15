from datetime import datetime
from typing import Iterable

from app.models.demand_task import DemandTask
from app.models.employee import Employee


def calculate_workforce_coverage(
    tasks: Iterable[DemandTask],
    employees: Iterable[Employee],
    window_start: datetime,
    window_end: datetime,
    available_headcount: int,
) -> tuple[list[dict], list[dict]]:
    """
    Calculate workforce coverage against demand.

    This version intentionally does NOT model shifts yet.
    It uses the employees supplied by the caller as the available workforce.

    Qualification matching is evaluated per employee against the
    qualifications required by the active task(s).
    """

    tasks = list(tasks)
    employees = list(employees)

    active_tasks = [
        task
        for task in tasks
        if task.start_time < window_end
        and task.end_time > window_start
        and task.status.value != "CANCELLED"
    ]

    eligible_employees = []

    for employee in employees:
        employee_qualification_ids = {
            employee_qualification.qualification_id
            for employee_qualification in employee.employee_qualifications
        }

        required_qualification_ids = set()

        for task in active_tasks:
            for qualification in task.required_qualifications:
                required_qualification_ids.add(qualification.id)

        missing_qualification_ids = (
            required_qualification_ids
            - employee_qualification_ids
        )

        eligible_employees.append(
            {
                "employee_id": employee.id,
                "employee_number": employee.employee_number,
                "employee_name": (
                    f"{employee.first_name} {employee.last_name}"
                ),
                "eligible": len(missing_qualification_ids) == 0,
                "missing_qualification_ids": list(
                    missing_qualification_ids
                ),
            }
        )

    intervals = _calculate_intervals(
        active_tasks=active_tasks,
        window_start=window_start,
        window_end=window_end,
        available_headcount=available_headcount,
    )

    return intervals, eligible_employees


def _calculate_intervals(
    active_tasks: list[DemandTask],
    window_start: datetime,
    window_end: datetime,
    available_headcount: int,
) -> list[dict]:

    if not active_tasks:
        return [
            _build_interval(
                start_time=window_start,
                end_time=window_end,
                target_demand=0,
                minimum_demand=0,
                available_headcount=available_headcount,
            )
        ]

    time_points = {
        window_start,
        window_end,
    }

    for task in active_tasks:
        task_start = max(task.start_time, window_start)
        task_end = min(task.end_time, window_end)

        time_points.add(task_start)
        time_points.add(task_end)

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
            if task.start_time < interval_end
            and task.end_time > interval_start
        ]

        target_demand = sum(
            task.target_headcount
            for task in overlapping_tasks
        )

        minimum_demand = sum(
            task.minimum_headcount
            for task in overlapping_tasks
        )

        intervals.append(
            _build_interval(
                start_time=interval_start,
                end_time=interval_end,
                target_demand=target_demand,
                minimum_demand=minimum_demand,
                available_headcount=available_headcount,
            )
        )

    return intervals


def _build_interval(
    start_time: datetime,
    end_time: datetime,
    target_demand: int,
    minimum_demand: int,
    available_headcount: int,
) -> dict:

    target_gap = max(
        0,
        target_demand - available_headcount,
    )

    minimum_gap = max(
        0,
        minimum_demand - available_headcount,
    )

    if target_demand <= available_headcount:
        status = "COVERED"
    elif minimum_demand <= available_headcount:
        status = "TARGET_NOT_COVERED"
    else:
        status = "MINIMUM_NOT_COVERED"

    return {
        "start_time": start_time,
        "end_time": end_time,
        "target_demand": target_demand,
        "minimum_demand": minimum_demand,
        "available_headcount": available_headcount,
        "target_gap": target_gap,
        "minimum_gap": minimum_gap,
        "status": status,
    }