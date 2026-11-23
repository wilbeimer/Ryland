"""Derive week ranges and assignment due dates from a course start_date."""

from datetime import UTC, date, datetime, time, timedelta, tzinfo
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


def calendar_week_range(due: datetime) -> tuple[date, date]:
    """ISO calendar week (Mon–Sun) containing the due datetime's local day.

    Uses the datetime's own offset when present; otherwise treats it as UTC so
    naive and aware values still bucket consistently.
    """
    if due.tzinfo is None:
        local = due.replace(tzinfo=UTC)
    else:
        local = due
    due_day = local.date()
    week_start = due_day - timedelta(days=due_day.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def start_date_from_due(
    due: datetime,
    week_number: int,
) -> date:
    """Infer course start_date so week N contains this due date's calendar day."""
    due_day = due.date()
    return due_day - timedelta(days=7 * (week_number - 1))


def due_datetime_for_assignment(
    start_date: date,
    week_number: int,
    assignment_type: AssignmentKind | object,
    provided: datetime | None = None,
    *,
    tz: tzinfo = UTC,
) -> datetime:
    """Pick a real due datetime inside the week.

    Prefer a provided due_date when its local calendar day (in `tz`) falls in
    the week. Otherwise text work lands on day 5 of the week and quizzes on
    the last day, so post-learning quizzes stay after text.

    Fallbacks are always timezone-aware (`tz`, default UTC) so stored values
    never mix naive and offset-carrying datetimes.
    """
    week_start, week_end = week_date_range(start_date, week_number)
    if provided is not None:
        if provided.tzinfo is None:
            local = provided.replace(tzinfo=tz)
        else:
            local = provided.astimezone(tz)
        due_day = local.date()
        if week_start <= due_day <= week_end:
            return local

    kind = getattr(assignment_type, "value", assignment_type)
    if kind == "quiz":
        due_day = week_end
    else:
        due_day = week_start + timedelta(days=4)
    return datetime.combine(due_day, time(23, 59), tzinfo=tz)
