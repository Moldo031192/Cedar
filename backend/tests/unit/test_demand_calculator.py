from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.demand_task import DemandTask, DemandTaskType, DemandTaskStatus
from app.schemas.demand_calculator import DemandCalculateRequest
from app.services.demand_calculator import calculate_demand_intervals


def _make_task(
    start_time,
    duration_minutes,
    target_headcount=10,
    minimum_headcount=8,
    status=DemandTaskStatus.PLANNED,
):
    return DemandTask(
        organization_id=None,
        flight_reference="TEST123",
        task_type=DemandTaskType.TURNAROUND,
        start_time=start_time,
        duration_minutes=duration_minutes,
        target_headcount=target_headcount,
        minimum_headcount=minimum_headcount,
        status=status,
    )


def test_no_tasks_returns_single_zero_demand_interval():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    intervals = calculate_demand_intervals(
        tasks=[],
        window_start=window_start,
        window_end=window_end,
        core_capacity=14,
        support_capacity=5,
    )

    assert len(intervals) == 1
    interval = intervals[0]
    assert interval["start_time"] == window_start
    assert interval["end_time"] == window_end
    assert interval["target_demand"] == 0
    assert interval["minimum_demand"] == 0
    assert interval["target_status"] == "CORE_COVERED"
    assert interval["minimum_status"] == "CORE_COVERED"


def test_single_task_fully_inside_window():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    task = _make_task(
        start_time=datetime(2026, 1, 1, 8, 30, tzinfo=timezone.utc),
        duration_minutes=30,
        target_headcount=10,
        minimum_headcount=8,
    )

    intervals = calculate_demand_intervals(
        tasks=[task],
        window_start=window_start,
        window_end=window_end,
        core_capacity=14,
        support_capacity=5,
    )

    assert len(intervals) == 3
    before, during, after = intervals

    assert before["target_demand"] == 0
    assert after["target_demand"] == 0

    assert during["start_time"] == task.start_time
    assert during["end_time"] == task.end_time
    assert during["target_demand"] == 10
    assert during["minimum_demand"] == 8
    assert during["target_status"] == "CORE_COVERED"


def test_overlapping_tasks_sum_demand():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    task_a = _make_task(
        start_time=datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc),
        duration_minutes=60,
        target_headcount=10,
        minimum_headcount=8,
    )
    task_b = _make_task(
        start_time=datetime(2026, 1, 1, 8, 30, tzinfo=timezone.utc),
        duration_minutes=60,
        target_headcount=6,
        minimum_headcount=4,
    )

    intervals = calculate_demand_intervals(
        tasks=[task_a, task_b],
        window_start=window_start,
        window_end=window_end,
        core_capacity=14,
        support_capacity=5,
    )

    overlap = [
        interval
        for interval in intervals
        if interval["start_time"] == datetime(2026, 1, 1, 8, 30, tzinfo=timezone.utc)
        and interval["end_time"] == datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
    ]
    assert len(overlap) == 1
    overlap_interval = overlap[0]

    assert overlap_interval["target_demand"] == 16
    assert overlap_interval["minimum_demand"] == 12
    assert overlap_interval["target_status"] == "SUPPORT_REQUIRED"


def test_task_clamped_to_window_boundaries():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)

    task = _make_task(
        start_time=datetime(2026, 1, 1, 7, 0, tzinfo=timezone.utc),
        duration_minutes=180,
        target_headcount=10,
        minimum_headcount=8,
    )

    intervals = calculate_demand_intervals(
        tasks=[task],
        window_start=window_start,
        window_end=window_end,
        core_capacity=14,
        support_capacity=5,
    )

    assert len(intervals) == 1
    interval = intervals[0]
    assert interval["start_time"] == window_start
    assert interval["end_time"] == window_end
    assert interval["target_demand"] == 10


def test_cancelled_task_is_excluded():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    task = _make_task(
        start_time=datetime(2026, 1, 1, 8, 30, tzinfo=timezone.utc),
        duration_minutes=30,
        target_headcount=10,
        minimum_headcount=8,
        status=DemandTaskStatus.CANCELLED,
    )

    intervals = calculate_demand_intervals(
        tasks=[task],
        window_start=window_start,
        window_end=window_end,
        core_capacity=14,
        support_capacity=5,
    )

    assert len(intervals) == 1
    assert intervals[0]["target_demand"] == 0
    assert intervals[0]["minimum_demand"] == 0


def test_minimum_demand_tracked_separately_from_target():
    window_start = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)

    task = _make_task(
        start_time=window_start,
        duration_minutes=60,
        target_headcount=25,
        minimum_headcount=16,
    )

    intervals = calculate_demand_intervals(
        tasks=[task],
        window_start=window_start,
        window_end=window_end,
        core_capacity=14,
        support_capacity=5,
    )

    assert len(intervals) == 1
    interval = intervals[0]
    assert interval["target_demand"] == 25
    assert interval["minimum_demand"] == 16
    assert interval["target_status"] == "DEFICIT"
    assert interval["minimum_status"] == "SUPPORT_REQUIRED"
    assert interval["target_gap"] == 25 - 19
    assert interval["minimum_gap"] == 0


def test_end_time_must_be_after_start_time():
    with pytest.raises(ValidationError):
        DemandCalculateRequest(
            organization_id="11111111-1111-1111-1111-111111111111",
            start_time=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc),
        )
