from backend.models import Course


def create_course(course: Course):
    return {
        "success": True,
        "course_id": "course_123",
        "message": f"Course '{course.name}' created successfully"
    }
