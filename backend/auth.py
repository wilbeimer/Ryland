from uuid import UUID

from backend.db import get_user_by_id


def get_current_user():
    user = get_user_by_id(str(UUID("00000000-0000-0000-0000-000000000001")))
    return user
