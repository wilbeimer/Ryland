import pytest

from backend.auth import get_current_user
from backend.db import get_user_by_id
from backend.endpoints import app

SEEDED_USER_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture(autouse=True)
def act_as_seed_user():
    """Keep existing API tests on the seeded user without a session token.

    Auth tests depend on this fixture and then remove the override.
    """

    def _user():
        return get_user_by_id(SEEDED_USER_ID)

    app.dependency_overrides[get_current_user] = _user
    yield
    app.dependency_overrides.pop(get_current_user, None)
