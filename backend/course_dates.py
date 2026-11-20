"""Derive week ranges and assignment due dates from a course start_date."""

from datetime import date, datetime, time, timedelta
from typing import Literal

DEFAULT_COURSE_COLOR = "#e5446d"
HEX_COLOR_PATTERN = r"^#[0-9A-Fa-f]{6}$"

AssignmentKind = Literal["text", "quiz"]


def week_date_range(start_date: date, week_number: int) -> tuple[date, date]:
    """Week N runs start_date + 7*(N-1) through start_date + 7*N - 1."""
    if week_number < 1:
        raise ValueError("week_number must be >= 1")
    week_start = start_date + timedelta(days=7 * (week_number - 1))
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def due_datetime_for_assignment(
    start_date: date,
    week_number: int,
    assignment_type: AssignmentKind | object,
    provided: datetime | None = None,
) -> datetime:
    """Pick a real due datetime inside the week.

    Prefer a provided due_date when it already falls in the week. Otherwise
    text work lands on day 5 of the week and quizzes on the last day, so
    post-learning quizzes stay after text.
    """
    week_start, week_end = week_date_range(start_date, week_number)
    if provided is not None:
        due_day = provided.date()
        if week_start <= due_day <= week_end:
            return provided

    kind = getattr(assignment_type, "value", assignment_type)
    if kind == "quiz":
        due_day = week_end
    else:
        due_day = week_start + timedelta(days=4)
    return datetime.combine(due_day, time(23, 59))
