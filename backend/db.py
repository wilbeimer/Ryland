import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta, tzinfo
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException

from backend.course_dates import (
    DEFAULT_COURSE_COLOR,
    calendar_week_range,
    start_date_from_due,
    week_date_range,
)

logger = logging.getLogger(__name__)
from backend.exceptions import (
    DuplicateEmailError,
    DuplicateUsernameError,
    DuplicateWeekError,
    InvalidAssignmentError,
    InvalidCourseError,
    InvalidQuizError,
    InvalidUserError,
    InvalidWeekError,
)
from backend.models import Assignment, Course, Quiz, User, Week

DB_PATH = Path(__file__).parent / "curriculum.db"
SEED_USER_ID = "00000000-0000-0000-0000-000000000001"
SEED_USERNAME = "test"
SEED_EMAIL = "test@mail.com"
SEED_PASSWORD = "password"


def dev_seed_enabled() -> bool:
    """True only when local dev explicitly opts in to the test/password account."""
    return os.getenv("RYLAND_DEV_SEED", "").strip() == "1"


@contextmanager
def get_conn(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.commit()
        conn.close()


def _parse_stored_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _backfill_course_start_dates(conn: sqlite3.Connection) -> None:
    """Set start_date from earliest due date minus that week's offset.

    Course has no created_at column, so courses with no assignments fall back
    to today. This keeps legacy week ranges aligned with stored due dates.
    """
    courses = conn.execute("SELECT id FROM Course").fetchall()
    today = date.today().isoformat()
    for course in courses:
        row = conn.execute(
            """
            SELECT a.due_date AS due_date, w.week_number AS week_number
            FROM Assignment a
            JOIN Week w ON a.week_id = w.id
            WHERE w.course_id = ?
            ORDER BY a.due_date ASC
            LIMIT 1
            """,
            (course["id"],),
        ).fetchone()
        if row is None:
            start = today
        else:
            due = _parse_stored_datetime(row["due_date"])
            start = start_date_from_due(due, int(row["week_number"])).isoformat()
        conn.execute(
            """
            UPDATE Course
            SET start_date = ?
            WHERE id = ?
            """,
            (start, course["id"]),
        )


def _ensure_user_columns(conn: sqlite3.Connection) -> None:
    """Add username and email_verified on databases created before sign-in."""
    columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(User)").fetchall()
    }
    if "username" not in columns:
        conn.execute("ALTER TABLE User ADD COLUMN username TEXT COLLATE NOCASE")
    if "email_verified" not in columns:
        conn.execute(
            "ALTER TABLE User ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0"
        )
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_user_username
        ON User(username COLLATE NOCASE)
        """)
    _promote_seed_user(conn)


def _promote_seed_user(conn: sqlite3.Connection) -> None:
    """Give an existing seed row username ``test`` and mark it verified.

    Runs only when ``RYLAND_DEV_SEED=1``. Does not insert a row and does not
    rehash the password.
    """
    if not dev_seed_enabled():
        return
    row = conn.execute(
        "SELECT username FROM User WHERE id = ?",
        (SEED_USER_ID,),
    ).fetchone()
    if row is None:
        return
    username = row["username"]
    if username is None or not str(username).strip():
        username = SEED_USERNAME
    conn.execute(
        """
        UPDATE User
        SET username = ?, email_verified = 1
        WHERE id = ?
        """,
        (username, SEED_USER_ID),
    )


def _ensure_course_columns(conn: sqlite3.Connection) -> None:
    """Add color/start_date for existing DBs without rewriting the table."""
    columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(Course)").fetchall()
    }
    if "color" not in columns:
        conn.execute(f"""
            ALTER TABLE Course
            ADD COLUMN color TEXT NOT NULL DEFAULT '{DEFAULT_COURSE_COLOR}'
            """)
    if "start_date" not in columns:
        # Nullable first, then backfill from due dates (not deploy-day).
        conn.execute("ALTER TABLE Course ADD COLUMN start_date TEXT")
        _backfill_course_start_dates(conn)


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS User (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password TEXT NOT NULL,
                username TEXT COLLATE NOCASE,
                email_verified INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS EmailVerification (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS Session (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS Course (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL CHECK (length(trim(name)) > 0),
                description TEXT NOT NULL,
                color TEXT NOT NULL DEFAULT '#e5446d',
                start_date TEXT NOT NULL DEFAULT (date('now')),
                FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_course_user ON Course(user_id);

            CREATE TABLE IF NOT EXISTS Week (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                week_number INTEGER NOT NULL CHECK (week_number >= 1),
                description TEXT NOT NULL,
                UNIQUE (course_id, week_number),
                FOREIGN KEY (course_id) REFERENCES Course(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS Assignment (
                id TEXT PRIMARY KEY,
                week_id TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('text', 'quiz')),
                name TEXT NOT NULL CHECK (length(trim(name)) > 0),
                description TEXT NOT NULL,
                rubric TEXT NOT NULL CHECK (json_valid(rubric)),
                due_date TEXT NOT NULL CHECK (julianday(due_date) IS NOT NULL),
                FOREIGN KEY (week_id) REFERENCES Week(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_assignment_week ON Assignment(week_id);

            CREATE TABLE IF NOT EXISTS Quiz (
                id TEXT PRIMARY KEY,
                assignment_id TEXT NOT NULL UNIQUE,
                time_limit INTEGER NOT NULL CHECK (time_limit > 0),
                questions TEXT NOT NULL CHECK (json_valid(questions)),
                FOREIGN KEY (assignment_id) REFERENCES Assignment(id) ON DELETE CASCADE
            );
            """)
        _ensure_user_columns(conn)
        _ensure_course_columns(conn)


# USERS
def get_user_by_id(id: str):
    with get_conn() as conn:
        row = conn.execute(
            """
                SELECT *
                FROM User
                WHERE id=?
            """,
            (id,),
        ).fetchone()
        if not row:
            raise HTTPException(401, "Couldn't identify the user")
        user = User.model_validate(dict(row))
    return user


def add_user_to_db(user: User):
    try:
        with get_conn() as conn:
            conn.execute(
                """
                    INSERT OR IGNORE INTO User
                    (id, email, password)
                    VALUES (?, ?, ?)
                """,
                (str(user.id), user.email, user.password.get_secret_value()),
            )
        return str(user.id)
    except sqlite3.IntegrityError as e:
        raise InvalidUserError("Invalid user details provided") from e


def _has_live_verification(conn: sqlite3.Connection, user_id: str, now: str) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM EmailVerification
        WHERE user_id = ?
          AND expires_at > ?
        """,
        (user_id, now),
    ).fetchone()
    return row is not None


def _raise_signup_conflict(conflict: sqlite3.Row, username: str) -> None:
    existing_username = conflict["username"] or ""
    if existing_username.lower() == username.lower():
        raise DuplicateUsernameError("That username is already taken")
    raise DuplicateEmailError("That email is already registered")


def _replaceable_signup(conn: sqlite3.Connection, row: sqlite3.Row, now: str) -> bool:
    """An unverified sign-up with an expired link and no courses can be reused.

    A legacy row that never received a token, or one that already owns a
    course, stays in place. Foreign keys are off, so those rows must not be
    deleted.
    """
    if row["email_verified"]:
        return False
    if not str(row["password"] or "").startswith("scrypt$"):
        return False
    if _has_live_verification(conn, row["id"], now):
        return False
    expired = conn.execute(
        """
        SELECT 1
        FROM EmailVerification
        WHERE user_id = ?
          AND expires_at <= ?
        LIMIT 1
        """,
        (row["id"], now),
    ).fetchone()
    if expired is None:
        return False
    course = conn.execute(
        "SELECT 1 FROM Course WHERE user_id = ? LIMIT 1",
        (row["id"],),
    ).fetchone()
    return course is None


def create_account(
    *,
    user_id: UUID,
    username: str,
    email: str,
    password_hash: str,
) -> UUID:
    """Insert a new account, or refresh one expired unverified sign-up.

    Returns the id that was stored. A refresh keeps the existing id and
    updates that row in place.
    """
    now = datetime.now(UTC).isoformat()
    with get_conn() as conn:
        conflicts = conn.execute(
            """
            SELECT id, username, email, email_verified, password
            FROM User
            WHERE username = ? COLLATE NOCASE
               OR email = ? COLLATE NOCASE
            """,
            (username, email),
        ).fetchall()
        replaceable: list[sqlite3.Row] = []
        for conflict in conflicts:
            if _replaceable_signup(conn, conflict, now):
                replaceable.append(conflict)
                continue
            _raise_signup_conflict(conflict, username)
        if len(replaceable) == 1:
            kept = replaceable[0]["id"]
            conn.execute(
                """
                UPDATE User
                SET email = ?, password = ?, username = ?, email_verified = 0
                WHERE id = ?
                """,
                (email, password_hash, username, kept),
            )
            return UUID(kept)
        if replaceable:
            _raise_signup_conflict(replaceable[0], username)
        try:
            conn.execute(
                """
                INSERT INTO User (id, email, password, username, email_verified)
                VALUES (?, ?, ?, ?, 0)
                """,
                (str(user_id), email, password_hash, username),
            )
        except sqlite3.IntegrityError as exc:
            message = str(exc).lower()
            if "username" in message:
                raise DuplicateUsernameError("That username is already taken") from exc
            if "email" in message:
                raise DuplicateEmailError("That email is already registered") from exc
            raise InvalidUserError("Invalid user details provided") from exc
        return user_id


def get_user_by_username(username: str) -> User | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, email, password, username, email_verified
            FROM User
            WHERE username = ? COLLATE NOCASE
            """,
            (username,),
        ).fetchone()
    if row is None:
        return None
    return User.model_validate(dict(row))


def update_user_password(user_id: UUID, password_hash: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE User SET password = ? WHERE id = ?",
            (password_hash, str(user_id)),
        )


def replace_verification_token(user_id: UUID, token_hash: str, expires_at: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM EmailVerification WHERE user_id = ?",
            (str(user_id),),
        )
        conn.execute(
            """
            INSERT INTO EmailVerification (token_hash, user_id, expires_at)
            VALUES (?, ?, ?)
            """,
            (token_hash, str(user_id), expires_at),
        )


def confirm_verification(token_hash: str, now: str) -> bool:
    """Mark the matching account verified. The token stays valid until expiry.

    A second confirm (for example React Strict Mode, or opening the link
    twice) still succeeds while the token is unexpired.
    """
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT user_id, expires_at
            FROM EmailVerification
            WHERE token_hash = ?
            """,
            (token_hash,),
        ).fetchone()
        if row is None:
            return False
        if row["expires_at"] <= now:
            conn.execute(
                "DELETE FROM EmailVerification WHERE token_hash = ?",
                (token_hash,),
            )
            return False
        conn.execute(
            "UPDATE User SET email_verified = 1 WHERE id = ?",
            (row["user_id"],),
        )
    return True


def insert_session(user_id: UUID, token_hash: str, expires_at: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO Session (token_hash, user_id, expires_at)
            VALUES (?, ?, ?)
            """,
            (token_hash, str(user_id), expires_at),
        )


def get_user_by_session_hash(token_hash: str) -> User | None:
    now = datetime.now(UTC).isoformat()
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT
                u.id AS id,
                u.email AS email,
                u.password AS password,
                u.username AS username,
                u.email_verified AS email_verified,
                s.expires_at AS expires_at
            FROM Session s
            JOIN User u ON u.id = s.user_id
            WHERE s.token_hash = ?
            """,
            (token_hash,),
        ).fetchone()
        if row is None:
            return None
        if row["expires_at"] <= now:
            conn.execute("DELETE FROM Session WHERE token_hash = ?", (token_hash,))
            return None
        data = {
            "id": row["id"],
            "email": row["email"],
            "password": row["password"],
            "username": row["username"],
            "email_verified": row["email_verified"],
        }
    return User.model_validate(data)


def delete_session_hash(token_hash: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM Session WHERE token_hash = ?", (token_hash,))


# COURSES
def add_course_to_db(course: Course):
    try:
        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO Course (id, user_id, name, description, color, start_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(course.id),
                    str(course.user_id),
                    course.name,
                    course.description,
                    course.color,
                    course.start_date.isoformat(),
                ),
            )
        return str(course.id)
    except sqlite3.IntegrityError as e:
        raise InvalidCourseError("Invalid course details provided") from e


def get_courses(user_id: UUID) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, name, description, color, start_date
            FROM Course
            WHERE user_id=?
            """,
            (str(user_id),),
        ).fetchall()
    return [dict(row) for row in rows]


def update_course_color(course_id: UUID, user_id: UUID, color: str) -> dict | None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE Course
            SET color=?
            WHERE id=?
            AND user_id=?
            """,
            (color, str(course_id), str(user_id)),
        )
        row = conn.execute(
            """
            SELECT id, name, description, color, start_date
            FROM Course
            WHERE id=?
            AND user_id=?
            """,
            (str(course_id), str(user_id)),
        ).fetchone()
    return dict(row) if row else None


def get_week_schedule_context(week_id: UUID) -> dict | None:
    """Return week_number and course start_date for due-date derivation."""
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT w.week_number AS week_number, c.start_date AS start_date
            FROM Week w
            JOIN Course c ON c.id = w.course_id
            WHERE w.id=?
            """,
            (str(week_id),),
        ).fetchone()
    if row is None:
        return None
    raw_start = row["start_date"]
    start = date.fromisoformat(raw_start) if raw_start else date.today()
    return {
        "week_number": int(row["week_number"]),
        "start_date": start,
    }


def delete_course_from_db(course_id: UUID, user_id: UUID) -> bool:
    """Delete a course owned by user_id, including weeks/assignments/quizzes.

    Explicit cleanup (not only FK CASCADE) so SQLite stays consistent even when
    PRAGMA foreign_keys is off, which is the default for this codebase.
    """
    with get_conn() as conn:
        owned = conn.execute(
            """
            SELECT id
            FROM Course
            WHERE id=?
            AND user_id=?
            """,
            (str(course_id), str(user_id)),
        ).fetchone()
        if owned is None:
            return False

        conn.execute(
            """
            DELETE FROM Quiz
            WHERE assignment_id IN (
                SELECT a.id
                FROM Assignment a
                JOIN Week w ON a.week_id = w.id
                WHERE w.course_id = ?
            )
            """,
            (str(course_id),),
        )
        conn.execute(
            """
            DELETE FROM Assignment
            WHERE week_id IN (
                SELECT id
                FROM Week
                WHERE course_id = ?
            )
            """,
            (str(course_id),),
        )
        conn.execute(
            "DELETE FROM Week WHERE course_id = ?",
            (str(course_id),),
        )
        conn.execute(
            """
            DELETE FROM Course
            WHERE id=?
            AND user_id=?
            """,
            (str(course_id), str(user_id)),
        )
        return True


# WEEKS
def add_week_to_db(week: Week) -> str:
    try:
        with get_conn() as conn:
            conn.execute(
                """
                INSERT
                INTO Week (id,
                           course_id,
                           week_number,
                           description)
                VALUES (?, ?, ?, ?)
                """,
                (str(week.id), str(week.course_id), week.week_number, week.description),
            )
        return str(week.id)
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE":
            raise DuplicateWeekError(
                "A week with this number already exists in the course"
            ) from e
        raise InvalidWeekError("Invalid week data provided") from e


def get_weeks(course_id: UUID) -> list[dict]:
    with get_conn() as conn:
        course = conn.execute(
            """
            SELECT start_date
            FROM Course
            WHERE id=?
            """,
            (str(course_id),),
        ).fetchone()
        rows = conn.execute(
            """
            SELECT id, course_id, week_number, description
            FROM Week
            WHERE course_id=?
            ORDER BY week_number
            """,
            (str(course_id),),
        ).fetchall()
    if course is None:
        return []
    raw_start = course["start_date"]
    start = date.fromisoformat(raw_start) if raw_start else date.today()
    result = []
    for row in rows:
        item = dict(row)
        week_start, week_end = week_date_range(start, int(item["week_number"]))
        item["start_date"] = week_start.isoformat()
        item["end_date"] = week_end.isoformat()
        result.append(item)
    return result


# ASSIGNMENTS
def add_assignment_to_db(assignment: Assignment) -> str:
    try:
        with get_conn() as conn:
            conn.execute(
                """
                INSERT
                INTO Assignment (id,
                                week_id,
                                type,
                                name,
                                description,
                                rubric,
                                due_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(assignment.id),
                    str(assignment.week_id),
                    assignment.type.value,
                    assignment.name,
                    assignment.description,
                    json.dumps(assignment.rubric),
                    assignment.due_date.isoformat(),
                ),
            )
            return str(assignment.id)
    except sqlite3.IntegrityError as e:
        raise InvalidAssignmentError("Invalid data for assignment") from e


def get_assignments(week_id: UUID) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, type, name, description, rubric, due_date
            FROM Assignment
            WHERE week_id=?
            ORDER BY CASE type WHEN 'text' THEN 0 WHEN 'quiz' THEN 1 ELSE 2 END,
                     due_date
            """,
            (str(week_id),),
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["rubric"] = json.loads(item["rubric"])
            result.append(item)
        return result


def _parse_due_for_calendar(value: str) -> datetime | None:
    try:
        due = datetime.fromisoformat(value)
    except ValueError:
        logger.warning("Skipping calendar row with malformed due_date: %s", value)
        return None
    if due.tzinfo is None:
        return due.replace(tzinfo=UTC)
    return due


def get_calendar_weeks(user_id: UUID, *, tz: tzinfo = UTC) -> list[dict]:
    """Group the user's assignments by ISO calendar week of due_date in `tz`."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
                a.id AS id,
                a.type AS type,
                a.name AS name,
                a.description AS description,
                a.rubric AS rubric,
                a.due_date AS due_date,
                c.id AS course_id,
                c.name AS course_name,
                c.color AS course_color
            FROM Assignment a
            JOIN Week w ON a.week_id = w.id
            JOIN Course c ON w.course_id = c.id
            WHERE c.user_id = ?
            """,
            (str(user_id),),
        ).fetchall()

    parsed: list[tuple[datetime, dict]] = []
    for row in rows:
        due = _parse_due_for_calendar(row["due_date"])
        if due is None:
            continue
        parsed.append(
            (
                due,
                {
                    "id": row["id"],
                    "type": row["type"],
                    "name": row["name"],
                    "description": row["description"],
                    "rubric": json.loads(row["rubric"]),
                    "due_date": row["due_date"],
                    "course_id": row["course_id"],
                    "course_name": row["course_name"],
                    "course_color": row["course_color"],
                },
            )
        )

    type_rank = {"text": 0, "quiz": 1}
    parsed.sort(
        key=lambda item: (
            item[0].astimezone(UTC),
            type_rank.get(item[1]["type"], 2),
            item[1]["name"],
        )
    )

    buckets: dict[date, dict] = {}
    for due, assignment in parsed:
        week_start, week_end = calendar_week_range(due, tz=tz)
        bucket = buckets.get(week_start)
        if bucket is None:
            bucket = {
                "start_date": week_start.isoformat(),
                "end_date": week_end.isoformat(),
                "assignments": [],
            }
            buckets[week_start] = bucket
        bucket["assignments"].append(assignment)
    return [buckets[key] for key in sorted(buckets)]


# QUIZZES
def add_quiz_to_db(quiz: Quiz) -> str:
    try:
        with get_conn() as conn:
            conn.execute(
                """
                INSERT
                INTO Quiz (id, assignment_id, time_limit, questions)
                VALUES (?, ?, ?, ?)
                """,
                (
                    str(quiz.id),
                    str(quiz.assignment_id),
                    int(quiz.time_limit.total_seconds()),
                    json.dumps([q.model_dump(mode="json") for q in quiz.questions]),
                ),
            )

            return str(quiz.id)
    except sqlite3.IntegrityError as e:
        raise InvalidQuizError("Invalid data for quiz") from e


def get_quiz(assignment_id: UUID) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, time_limit, questions
            FROM Quiz
            WHERE assignment_id=?
            """,
            (str(assignment_id),),
        ).fetchone()
        if row is None:
            raise HTTPException(404, "No quiz found for this assignment")
        item = dict(row)
        item["questions"] = json.loads(item["questions"])
        item["time_limit"] = timedelta(seconds=item["time_limit"])
        return item


# OWNERSHIP
def get_owned_course(course_id: UUID, user_id: UUID):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT c.id
            FROM Course c
            WHERE c.id=?
            AND c.user_id=?
            """,
            (
                str(course_id),
                str(user_id),
            ),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Course not found")
        return row


def get_owned_week(week_id: UUID, user_id: UUID):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT w.id
            FROM Week w, Course c
            WHERE w.course_id=c.id
            AND w.id=?
            AND c.user_id=?
            """,
            (
                str(week_id),
                str(user_id),
            ),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Week not found")
        return row


def get_owned_assignment(assignment_id: UUID, user_id: UUID):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT a.id
            FROM Assignment a, Week w, Course c
            WHERE a.week_id=w.id
            AND w.course_id=c.id
            AND a.id=?
            AND c.user_id=?
            """,
            (
                str(assignment_id),
                str(user_id),
            ),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Assigment not found")
        return row


def get_assignment_detail(assignment_id: UUID, user_id: UUID) -> dict:
    """Assignment plus owning course name/color for the detail page."""
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT
                a.id AS id,
                a.type AS type,
                a.name AS name,
                a.description AS description,
                a.rubric AS rubric,
                a.due_date AS due_date,
                c.id AS course_id,
                c.name AS course_name,
                c.color AS course_color
            FROM Assignment a
            JOIN Week w ON a.week_id = w.id
            JOIN Course c ON w.course_id = c.id
            WHERE a.id = ?
              AND c.user_id = ?
            """,
            (str(assignment_id), str(user_id)),
        ).fetchone()
        if row is None:
            raise HTTPException(404, "Assignment not found")
        item = dict(row)
        item["rubric"] = json.loads(item["rubric"])
        return item


def ensure_seed_user() -> None:
    """Insert the local seed account when ``RYLAND_DEV_SEED=1``.

    With the flag unset this only creates the schema. It does not add or
    verify the well-known ``test`` / ``password`` account.
    """
    from backend.passwords import hash_password, is_password_hash

    init_db()
    if not dev_seed_enabled():
        return
    with get_conn() as conn:
        row = conn.execute(
            "SELECT password FROM User WHERE id = ?",
            (SEED_USER_ID,),
        ).fetchone()
        if row is None:
            conn.execute(
                """
                INSERT INTO User (id, email, password, username, email_verified)
                VALUES (?, ?, ?, ?, 1)
                """,
                (
                    SEED_USER_ID,
                    SEED_EMAIL,
                    hash_password(SEED_PASSWORD),
                    SEED_USERNAME,
                ),
            )
            return
        if not is_password_hash(row["password"]):
            conn.execute(
                "UPDATE User SET password = ? WHERE id = ?",
                (hash_password(row["password"]), SEED_USER_ID),
            )


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    ensure_seed_user()
