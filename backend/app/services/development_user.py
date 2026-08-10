"""Temporary development-user mechanism.

Authentication does not exist yet, but every owned resource (subjects,
topics, ...) needs an owner. Until the authentication phase, this module
resolves a single known development user, creating it on first use.

To replace with real authentication later, swap the dependency in the
route layer for a real ``get_current_user()`` — every other layer already
works from a plain ``User`` object.
"""

from sqlalchemy.orm import Session

from app.models import User

DEVELOPMENT_USER_EMAIL = "dev@bytebrains.local"
DEVELOPMENT_USER_NAME = "Development User"


def get_current_development_user(db: Session) -> User:
    """Return the development user, creating it if it does not exist yet.

    This is intentionally deterministic: all requests during development
    act as the same user.
    """
    user = (
        db.query(User)
        .filter(User.email == DEVELOPMENT_USER_EMAIL)
        .first()
    )
    if user is None:
        user = User(name=DEVELOPMENT_USER_NAME, email=DEVELOPMENT_USER_EMAIL)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user