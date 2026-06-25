"""One-off CLI to bootstrap (or promote) an admin account.

Usage:
    python -m scripts.create_admin admin@m-motors.fr "StrongPassword123"

Registration via /auth/register always creates a 'client' role by design
(an unauthenticated endpoint must never be able to grant admin rights).
This script is the deliberate, explicit way to create the first back-office
account, run once after deployment with database access.
"""

import sys

from app.database import SessionLocal
from app.models import Role, User
from app.security import hash_password


def main(email: str, password: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(email=email, hashed_password=hash_password(password), role=Role.admin)
            db.add(user)
            print(f"Created admin account: {email}")
        else:
            user.role = Role.admin
            user.hashed_password = hash_password(password)
            print(f"Promoted existing account to admin and reset password: {email}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m scripts.create_admin <email> <password>")
        raise SystemExit(1)
    main(sys.argv[1], sys.argv[2])
