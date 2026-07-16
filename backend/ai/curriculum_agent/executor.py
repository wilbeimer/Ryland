import uuid
from pydantic import ValidationError

from backend.models import (
    RylandState,
    Week,
    Assignment,
    AssignmentType,
    Quiz,
    QuizType,
    Question,
    QuestionType,
    Resource,
    ResourceSource,
    Textbook,
    CourseStatus,
)
from backend.ai.youtube import search_youtube as _search_youtube_api

# --- Lookups ---


def _find_week(state: RylandState, week_number: int) -> Week | None:
    for week in state.course.weeks:
        if week.number == week_number:
            return week
    return None


# --- Tool implementations ---


def set_course_description(
    state: RylandState,
    description: str,
    domain: str | None = None,
    subdomains: list[str] | None = None,
    prerequisites: list[str] | None = None,
) -> dict:
    state.course.description = description
    if domain is not None:
        state.course.domain = domain
    if subdomains is not None:
        state.course.subdomains = subdomains
    if prerequisites is not None:
        state.course.prerequisites = prerequisites
    return {"status": "ok"}


def set_course_length(
    state: RylandState, duration_weeks: int, hours_per_week: int
) -> dict:
    state.course.duration_weeks = duration_weeks
    state.course.hours_per_week = hours_per_week
    return {"status": "ok"}


def set_textbook(
    state: RylandState,
    title: str,
    authors: list[str],
    edition: str | None = None,
    publisher: str | None = None,
    isbn: str | None = None,
    link: str | None = None,
) -> dict:
    try:
        state.course.textbook = Textbook(
            title=title,
            authors=authors,
            edition=edition,
            publisher=publisher,
            isbn=isbn,
            link=link,
        )
    except ValidationError as e:
        return {"error": str(e)}
    return {"status": "ok"}


def create_week(
    state: RylandState, week_number: int, goal: str, topics: list[str]
) -> dict:
    if _find_week(state, week_number) is not None:
        return {
            "error": f"Week {week_number} already exists. Reuse it, don't recreate it."
        }
    try:
        week = Week(id=str(uuid.uuid4()), number=week_number, goal=goal, topics=topics)
    except ValidationError as e:
        return {"error": str(e)}
    state.course.weeks.append(week)
    state.course.weeks.sort(key=lambda w: w.number)
    return {"status": "ok", "week_id": week.id}


def create_assignment(
    state: RylandState,
    week_number: int,
    title: str,
    type: str,
    description: str,
    requirements: list[str] | None = None,
    resources: list[dict] | None = None,
    dueDate: str = "",
    points: float = 100,
    rubric: str = "",
) -> dict:
    week = _find_week(state, week_number)
    if week is None:
        return {"error": f"No week {week_number} yet. Call create_week first."}
    try:
        resource_objs = [
            Resource(
                title=r["title"],
                url=r["url"],
                source=ResourceSource(r.get("source", "article")),
            )
            for r in (resources or [])
        ]
        assignment = Assignment(
            id=str(uuid.uuid4()),
            title=title,
            type=AssignmentType(type),
            description=description,
            requirements=requirements or [],
            resources=resource_objs,
            dueDate=dueDate,
            points=points,
            rubric=rubric,
        )
    except (ValidationError, ValueError, KeyError) as e:
        return {"error": str(e)}
    week.assignments.append(assignment)
    return {"status": "ok", "assignment_id": assignment.id}


def create_quiz(
    state: RylandState,
    week_number: int,
    title: str,
    type: str,
    questions: list[dict],
    dueDate: str = "",
    points: float = 100,
    replace: bool = False,
) -> dict:
    week = _find_week(state, week_number)
    if week is None:
        return {"error": f"No week {week_number} yet. Call create_week first."}
    if week.quiz is not None and not replace:
        return {
            "error": f"Week {week_number} already has a quiz ('{week.quiz.title}'). "
            f"Pass replace=true if you intend to overwrite it."
        }
    try:
        question_objs = [
            Question(
                type=QuestionType(q["type"]),
                prompt=q["prompt"],
                choices=q.get("choices", []),
                answer=q["answer"],
            )
            for q in questions
        ]
        quiz = Quiz(
            id=str(uuid.uuid4()),
            title=title,
            type=QuizType(type),
            questions=question_objs,
            dueDate=dueDate,
            points=points,
        )
    except (ValidationError, ValueError, KeyError) as e:
        return {"error": str(e)}
    week.quiz = quiz
    return {"status": "ok", "quiz_id": quiz.id}


def search_youtube(state: RylandState, query: str, max_results: int = 2) -> dict:
    try:
        results = _search_youtube_api(query, max_results=max_results)
    except Exception as e:
        return {"error": f"YouTube search failed: {e}"}
    return {"results": results}


def finish_course(state: RylandState) -> dict:
    missing = []
    if not state.course.weeks:
        missing.append("no weeks created")
    for week in state.course.weeks:
        if not week.assignments:
            missing.append(f"week {week.number} has no assignments")
    if missing:
        return {"error": "Course not complete yet: " + "; ".join(missing)}
    state.course.status = CourseStatus.COMPLETE
    return {"status": "complete", "week_count": state.course.week_count}


TOOL_FUNCTIONS = {
    "set_course_description": set_course_description,
    "set_course_length": set_course_length,
    "set_textbook": set_textbook,
    "create_week": create_week,
    "create_assignment": create_assignment,
    "create_quiz": create_quiz,
    "search_youtube": search_youtube,
    "finish_course": finish_course,
}


def execute_tool(name: str, arguments: dict, state: RylandState) -> dict:
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return {"error": f"Unknown tool '{name}'"}
    try:
        return fn(state, **arguments)
    except TypeError as e:
        return {"error": f"Bad arguments for {name}: {e}"}
