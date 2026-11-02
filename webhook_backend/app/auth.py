from datetime import datetime, timedelta, timezone
from uuid import UUID
import secrets

import jwt

from pwdlib import PasswordHash

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db, settings
from app.models import Agent

from sqlalchemy.exc import IntegrityError
from app.schemas import AgentRegisterRequest


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)

password_hasher = PasswordHash.recommended()

security = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30



def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:

    return password_hasher.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(agent_id: UUID):

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(agent_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=ALGORITHM,
    )

@router.post("/register", status_code=201)
def register_agent(
    data: AgentRegisterRequest,
    db: Session = Depends(get_db),
):
    # 1. Validate company invitation code
    if not secrets.compare_digest(
        data.invite_code,
        settings.agent_invite_code,
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid company invitation code",
        )

    # 2. Normalize email
    email = data.email.strip().lower()

    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise HTTPException(
            status_code=422,
            detail="Invalid email address",
        )

    # 3. Check whether the email is already registered
    existing_agent = db.scalar(
        select(Agent).where(Agent.email == email)
    )

    if existing_agent:
        raise HTTPException(
            status_code=409,
            detail="An agent with this email already exists",
        )

    # 4. Hash password and create agent
    agent = Agent(
        email=email,
        password_hash=password_hasher.hash(data.password),
        is_active=True,
    )

    try:
        db.add(agent)
        db.commit()
        db.refresh(agent)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An agent with this email already exists",
        )

    return {
        "status": "created",
        "message": "Agent account created successfully. Please sign in.",
        "agent": {
            "id": str(agent.id),
            "email": agent.email,
        },
    }

@router.post("/login")
def agent_login(
    credentials: dict,
    db: Session = Depends(get_db),
):

    email = credentials.get("email")
    password = credentials.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        raise HTTPException(
            status_code=422,
            detail="Email and password are required",
        )

    agent = db.scalar(
        select(Agent).where(
            Agent.email == email.strip().lower()
        )
    )

    if (
        agent is None
        or not agent.is_active
        or not verify_password(password, agent.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(agent.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "agent": {
            "id": str(agent.id),
            "email": agent.email,
        },
    }


def get_current_agent(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
):

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[ALGORITHM],
        )

        agent_id = UUID(payload["sub"])

    except (jwt.InvalidTokenError, ValueError, KeyError, TypeError):

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    agent = db.get(Agent, agent_id)

    if agent is None or not agent.is_active:
        raise HTTPException(
            status_code=401,
            detail="Agent account is unavailable",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return agent

def create_customer_access_token(
    conversation_id: UUID,
    customer_id: UUID,
):
    expire = datetime.now(timezone.utc) + timedelta(hours=24)

    payload = {
        "sub": str(customer_id),
        "conversation_id": str(conversation_id),
        "token_type": "customer",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=ALGORITHM,
    )