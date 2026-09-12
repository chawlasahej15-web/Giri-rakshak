import argparse
import os
import secrets
from pathlib import Path
import pandas as pd
from models import Zone
from sqlalchemy.orm import Session

from auth import hash_password
from database import Base, SessionLocal, engine
from models import User


def main():
    parser = argparse.ArgumentParser(description="Seed Giri-Rakshak demo official account")
    parser.add_argument("--email", default=os.getenv("SEED_OFFICIAL_EMAIL", "official@girirakshak.local"))
    parser.add_argument("--password", default=os.getenv("SEED_OFFICIAL_PASSWORD"))
    parser.add_argument("--name", default="District Disaster Management Officer")
    parser.add_argument("--department", default="Disaster Management")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    password = args.password or secrets.token_urlsafe(12)

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == args.email.lower()).first()
        if user:
            user.full_name = args.name
            user.role = "official"
            user.department = args.department
            user.password_hash = hash_password(password)
            user.is_active = True
            action = "updated"
        else:
            user = User(
                full_name=args.name,
                email=args.email.lower(),
                password_hash=hash_password(password),
                role="official",
                department=args.department,
                is_active=True,
            )
            db.add(user)
            action = "created"

            db.commit()
        print("=" * 60)
        print("GIRI-RAKSHAK OFFICIAL SEED")
        print("=" * 60)
        print(f"Action   : {action}")
        print(f"Email    : {args.email.lower()}")
        print(f"Password : {password}")
        print("Role     : official")
        print("Store these credentials only for your demo/testing account.")
    finally:

        db.close()


if __name__ == "__main__":
    main()
