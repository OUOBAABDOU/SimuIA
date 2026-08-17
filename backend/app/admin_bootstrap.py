"""Create or promote an administrator without placing credentials in source control.

Usage:
  ADMIN_BOOTSTRAP_PASSWORD='...' python -m app.admin_bootstrap --email admin@example.com
"""

from __future__ import annotations

import argparse
import asyncio
import os

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.modules.auth.security import hash_password
from app.modules.candidates.models import User, UserRole


async def main(email: str) -> None:
    password = os.getenv("ADMIN_BOOTSTRAP_PASSWORD")
    if not password or len(password) < 12:
        raise SystemExit("ADMIN_BOOTSTRAP_PASSWORD must contain at least 12 characters")
    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == email.lower()).with_for_update())
        if user is None:
            user = User(email=email.lower(), password_hash=hash_password(password), role=UserRole.ADMIN)
            db.add(user)
        else:
            user.password_hash = hash_password(password)
            user.role = UserRole.ADMIN
            user.token_version += 1
        await db.commit()
    print(f"Administrator ready: {email.lower()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    asyncio.run(main(args.email))
