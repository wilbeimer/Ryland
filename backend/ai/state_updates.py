from uuid import uuid4
from backend.models import Assignment, Quiz, RylandState, Textbook, Week


def apply_description(result: dict, state: RylandState) -> None:
    course = state.course

    course.description = result["description"]
    course.domain = result["domain"]
    course.subdomains = result["subdomains"]
    course.prerequisites = result["prerequisites"]


def apply_resources(result: dict, state: RylandState) -> None:
    if "textbook" in result:
        state.course.textbook = Textbook.model_validate(result["textbook"])


def apply_course_length(result, state):
    state.course.duration_weeks = result["duration_weeks"]
    state.course.hours_per_week = result["hours_per_week"]


def apply_weeks(result: dict, state: RylandState) -> None:
    state.course.weeks = [
        Week(
            id=str(uuid4()),
            number=week["week"],
            goal=week["goal"],
            topics=week["topics"],
        )
        for week in result["weekly_goals"]
    ]


def apply_assignments(result: dict, state: RylandState) -> None:
    weeks = {week.number: week for week in state.course.weeks}

    for assignment in result["assignments"]:
        weeks[assignment["week"]].assignments.append(
            Assignment(
                id=str(uuid4()),
                title=assignment["title"],
                type=assignment["type"],
                description=assignment["description"],
                requirements=assignment["requirements"],
            )
        )


def apply_quizzes(result, state):
    weeks = {week.number: week for week in state.course.weeks}

    for quiz in result["quizzes"]:
        weeks[quiz["week"]].quiz = Quiz(
            id=str(uuid4()),
            title=quiz["title"],
            type=quiz["type"],
            questions=quiz["questions"]
        )
