"""
Pytest configuration and test database fixtures using in-memory/test SQLite engine.
"""
import asyncio
import os
import sys
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.core.config import settings
from app.core.database import AsyncSessionLocal, Base, engine, init_db
from app.main import app
from app.models.department import Department
from app.models.drone import Drone, DroneStation
from app.models.user import User
from app.core.security import hash_password, create_access_token


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    await init_db()
    yield
    # Cleanup


@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def officer_token(db_session):
    # Ensure officer exists
    from sqlalchemy import select
    res = await db_session.execute(select(User).where(User.email == "test_officer@disaster.org"))
    officer = res.scalar_one_or_none()
    if not officer:
        officer = User(
            name="Test Officer",
            email="test_officer@disaster.org",
            password_hash=hash_password("Password123!"),
            role="officer",
            is_active=True,
        )
        db_session.add(officer)
        await db_session.commit()
        await db_session.refresh(officer)

    token = create_access_token(subject=officer.id, role="officer")
    return token, officer


@pytest_asyncio.fixture
async def pilot_token(db_session):
    from sqlalchemy import select
    res = await db_session.execute(select(User).where(User.email == "test_pilot@rescue.org"))
    pilot = res.scalar_one_or_none()
    if not pilot:
        pilot = User(
            name="Test Pilot",
            email="test_pilot@rescue.org",
            password_hash=hash_password("Password123!"),
            role="pilot",
            is_active=True,
        )
        db_session.add(pilot)
        await db_session.commit()
        await db_session.refresh(pilot)

    token = create_access_token(subject=pilot.id, role="pilot")
    return token, pilot
