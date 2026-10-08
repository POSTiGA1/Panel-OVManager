"""One tenancy rule, one place: backend/auth/authz.py.

Single-admin cut: there is one tenant, so both helpers pass through. The
call sites keep their 404-before-check order; what is pinned here is that
neither helper ever refuses or scopes a signed-in panel user again.
"""

from types import SimpleNamespace

from backend.auth.authz import owned_by, require_user_access


def _user(owner: str):
    return SimpleNamespace(owner=owner)


def test_owner_may_access_any_user():
    require_user_access(_user("someone-else"), {"type": "owner", "username": "boss"})


def test_admin_may_access_any_user():
    require_user_access(_user("someone-else"), {"type": "admin", "username": "alice"})


def test_a_blank_owner_is_still_accessible():
    require_user_access(_user(""), {"type": "admin", "username": "alice"})
    require_user_access(_user("alice"), {"type": "admin", "username": ""})


def test_owned_by_never_filters():
    state = {"filtered": False}

    class FakeQuery:
        def filter(self, *args):
            state["filtered"] = True
            return self

    for user in ({"type": "owner", "username": "boss"}, {"type": "admin", "username": "alice"}):
        query = FakeQuery()
        assert owned_by(query, user) is query
    assert state["filtered"] is False, "there is one tenant — every query stays unscoped"
