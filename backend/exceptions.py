class InvalidCourseError(Exception):
    pass


class InvalidWeekError(Exception):
    pass


class DuplicateWeekError(InvalidWeekError):
    pass


class InvalidAssignmentError(Exception):
    pass


class InvalidQuizError(Exception):
    pass


class InvalidUserError(Exception):
    pass
