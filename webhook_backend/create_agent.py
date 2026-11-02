from getpass import getpass

from sqlalchemy import select

from app.database import SessionLocal, Base, engine
from app import models
from app.models import Agent
from app.auth import password_hasher

# Create any missing tables
Base.metadata.create_all(bind=engine)
def create_agent():

    email = input("Enter agent email: ").strip().lower()
    password = getpass("Enter agent password: ")

    if not email or not password:
        print("Email and password cannot be empty.")
        return

    if len(password) < 12:
        print("Password must contain at least 12 characters.")
        return

    db = SessionLocal()

    try:

        existing = db.scalar(
            select(Agent).where(Agent.email == email)
        )

        if existing:
            print("Agent already exists.")
            return

        agent = Agent(
            email=email,
            password_hash=password_hasher.hash(password),
            is_active=True,
        )

        db.add(agent)
        db.commit()

        print("Agent account created successfully!")

    except Exception:

        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    create_agent()