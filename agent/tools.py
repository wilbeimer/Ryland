from uuid import UUID, uuid4
from backend.db import InvalidAssignmentError, InvalidCourseError, InvalidWeekError, add_assignment_to_db, add_course_to_db, add_week_to_db
from backend.models import Assignment, Course, Week


TOOLS = [
    {
        "name": "create_course",
        "description": (
            "Creates a new course and adds it to the database. "
                "Returns the new course_id, which is required by create_week."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "course_name": {
                    "type": "string",
                    "description": "The name of the course"
                },
                "course_description": {
                    "type": "string",
                    "description": "A detailed description of the course"
                }
            },
            "required": ["course_name", "course_description"]
        }
    },
    {
        "name": "create_week",
        "description": (
            "Creates a new week within a course and adds it to the database. "
                "Returns the new week_id, which is required by create_assignment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "course_id": {
                    "type": "string",
                    "description": "The course_id returned by create_course"
                },
                "week_number": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Position of this week in the course, starting at 1"
                },
                "week_description": {
                    "type": "string",
                    "description": "What this week covers: topics, goals, and any key concepts"
                }
            },
            "required": ["course_id", "week_number", "week_description"]
        }
    },
    {
        "name": "create_assignment",
        "description": (
            "Creates a new assignment within a week and adds it to the database. "
                "Returns the new assignment_id. If assignment_type is 'quiz', "
                "follow up with create_quiz using that assignment_id."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "week_id": {
                    "type": "string",
                    "description": "The week_id returned by create_week"
                },
                "assignment_type": {
                    "type": "string",
                    "enum": ["text", "quiz"],
                    "description": (
                        "'text' for a written response the student writes freely, "
                            "'quiz' for a set of questions"
                    )
                },
                "assignment_name": {
                    "type": "string",
                    "description": "A short title for the assignment"
                },
                "assignment_description": {
                    "type": "string",
                    "description": "Instructions shown to the student"
                },
                "rubric": {
                    "type": "object",
                    "description": "The grading rubric used to evaluate submissions",
                    "properties": {
                        "criteria": {
                            "type": "array",
                            "description": "The individual criteria submissions are graded against",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "Short name of the criterion"
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "What full credit looks like for this criterion"
                                    },
                                    "points": {
                                        "type": "number",
                                        "description": "Maximum points for this criterion"
                                    }
                                },
                                "required": ["name", "description", "points"]
                            }
                        }
                    },
                    "required": ["criteria"]
                },
                "due_date": {
                    "type": "string",
                    "description": (
                        "Due date and time in ISO 8601 with a timezone offset, "
                            "e.g. 2026-10-15T23:59:00-04:00"
                    )
                }
            },
            "required": [
                "week_id",
                "assignment_type",
                "assignment_name",
                "assignment_description",
                "rubric",
                "due_date"
            ]
        }
    },
    {
        "name": "create_quiz",
        "description": (
            "Creates a quiz and its questions for an existing assignment whose "
                "assignment_type is 'quiz'. Do not use this for text assignments."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "assignment_id": {
                    "type": "string",
                    "description": "The assignment_id returned by create_assignment"
                },
                "time_limit_minutes": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "How long the student has to complete the quiz, in minutes"
                },
                "questions": {
                    "type": "array",
                    "minItems": 1,
                    "description": "The quiz questions, in the order they should appear",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question_type": {
                                "type": "string",
                                "enum": ["short answer", "multiple choice"],
                                "description": "The format of the question"
                            },
                            "prompt": {
                                "type": "string",
                                "description": "The question text shown to the student"
                            },
                            "options": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": (
                                    "The answer choices. Only for multiple choice questions; "
                                        "omit for short answer"
                                )
                            },
                            "correct_answer": {
                                "type": "string",
                                "description": (
                                    "The correct answer. For multiple choice, it must exactly "
                                        "match one of the options. For short answer, the expected "
                                        "answer or key points the grader should look for"
                                )
                            }
                        },
                        "required": ["question_type", "prompt", "correct_answer"]
                    }
                }
            },
            "required": ["assignment_id", "time_limit_minutes", "questions"]
        }
    },
    {
        "name": "ask_user",
        "description": "Ask the user a clarifying question when the request is missing information you need. Use this tool any time you need clarification or missing information from the user before proceeding. Do not ask the user questions in plain text — always use this tool.",
        "input_schema": {
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
    },
]


def create_course(tool_input, user_id: UUID) -> tuple[dict[str, str], bool]:
    course_id = uuid4()
    try:
        course = Course(
            id=course_id,
            user_id=user_id,
            name=tool_input["course_name"],
            desc=tool_input["course_description"]
        )
        course_id = add_course_to_db(course=course)
        return {"course_id": course_id}, False
    except InvalidCourseError as e:
        return {"content": str(e)}, True
    except KeyError as e:
        return {"content": f"Missing required fields {e}"}, True


def create_week(tool_input) -> tuple[dict[str, str], bool]:
    week_id = uuid4()
    try:
        week = Week(
            id=week_id,
            course_id=tool_input["course_id"],
            week_number=tool_input["week_number"],
            desc=tool_input["week_description"]
        )
        week_id = add_week_to_db(week=week)
        return {"week_id": week_id}, False
    except InvalidWeekError as e:
        return {"content": str(e)}, True
    except KeyError as e:
        return {"content": f"Missing required fields {e}"}, True


def create_assignment(tool_input) -> tuple[dict[str, str], bool]:
    assignment_id = uuid4()
    try:
        assignment = Assignment(
            id=assignment_id,
            week_id=tool_input["week_id"],
            type=tool_input["assignment_type"],
            name=tool_input["assignment_name"],
            desc=tool_input["assignment_description"],
            rubric=tool_input["rubric"],
            due_date=tool_input["due_date"]
        )
        assignment_id = add_assignment_to_db(assignment=assignment)
        return {"assignment_id": assignment_id}, False
    except InvalidAssignmentError as e:
        return {"content": str(e)}, True
    except KeyError as e:
        return {"content": f"Missing required fields {e}"}, True


def create_quiz(tool_input) -> tuple[dict[str, str], bool]:
    return {"tool ran": "still in development"}, False


def ask_user(tool_input) -> tuple[str, bool]:
    answer = input(f"\n{tool_input['question']}\n> ")
    return answer, False
