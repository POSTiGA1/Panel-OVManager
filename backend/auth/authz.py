"""Role-based and ownership-based FastAPI authorization dependencies."""

from fastapi import Depends, HTTPException, status

from backend.auth.auth import get_current_user


def require_owner(user: dict = Depends(get_current_user)):
    if user.get("type") != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires owner privileges",
        )
    return user


def require_user_access(db_user, current_user: dict) -> None:
    """Single-tenant pass-through: every signed-in panel user may touch any user.

    Call it after loading the row so the call sites keep their 404-before-check
    order; there is one tenant, so no refusal is possible here.
    """
    return None


def owned_by(query, current_user: dict):
    """The list counterpart of :func:`require_user_access`."""
    return query
