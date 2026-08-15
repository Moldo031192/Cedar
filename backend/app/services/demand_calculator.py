from datetime import datetime
from typing import Iterable

from app.models.demand_task import DemandTask


def calculate_demand_intervals(
    tasks: Iterable[DemandTask],
    window_start: datetime,
    window_end: datetime,
    core_capacity: int = 14,
    support_capacity: int = 5,
) -> list[dict]:
    """
    Calculate simultaneous staffing demand for a time window.

    Each active DemandTask contributes:
        target_headcount
        minimum_headcount

    to every interval in which that task is active.
    """

    tasks = list(tasks)

    # Keep only tasks that actually overlap the requested window.
    active_tasks = [
        task
        for task in tasks
        if task.start_time < window_end
        and task.end_time > window_start
        and task.status.value != "CANCELLED"
    ]

    total_capacity = core_capacity + support_capacity

    # No tasks at all: return one zero-demand interval.
    if not active_tasks:
        return [
            _build_interval(
                start_time=window_start,
                end_time=window_end,
                target_demand=0,
                minimum_demand=0,
                core_capacity=core_capacity,
                support_capacity=support_capacity,
                total_capacity=total_capacity,
            )
        ]

    # Demand can only change at:
    # - window start
    # - window end
    # - task start
    # - task end
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
                core_capacity=core_capacity,
                support_capacity=support_capacity,
                total_capacity=total_capacity,
            )
        )

    return intervals


def _build_interval(
    start_time: datetime,
    end_time: datetime,
    target_demand: int,
    minimum_demand: int,
    core_capacity: int,
    support_capacity: int,
    total_capacity: int,
) -> dict:
    target_gap = max(
        0,
        target_demand - total_capacity,
    )

    minimum_gap = max(
        0,
        minimum_demand - total_capacity,
    )

    if target_demand <= core_capacity:
        target_status = "CORE_COVERED"
    elif target_demand <= total_capacity:
        target_status = "SUPPORT_REQUIRED"
    else:
        target_status = "DEFICIT"

    if minimum_demand <= core_capacity:
        minimum_status = "CORE_COVERED"
    elif minimum_demand <= total_capacity:
        minimum_status = "SUPPORT_REQUIRED"
    else:
        minimum_status = "DEFICIT"

    return {
        "start_time": start_time,
        "end_time": end_time,
        "target_demand": target_demand,
        "minimum_demand": minimum_demand,
        "core_capacity": core_capacity,
        "support_capacity": support_capacity,
        "total_capacity": total_capacity,
        "target_gap": target_gap,
        "minimum_gap": minimum_gap,
        "target_status": target_status,
        "minimum_status": minimum_status,
    }