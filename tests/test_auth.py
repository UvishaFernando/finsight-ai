"""
Auth endpoint tests — run with: pytest tests/ -v
These test the full register → login → protected route flow.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base, get_db

# Use in-memory SQLite for tests (no PostgreSQL needed)
SQLITE_URL = "sqlite:///./test_finsight.db"
engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)

TEST_USER = {
    "email": "test@finsight.lk",
    "full_name": "Test User",
    "password": "TestPass123"
}


class TestRegister:
    def test_register_success(self):
        res = client.post("/api/v1/auth/register", json=TEST_USER)
        assert res.status_code == 201
        data = res.json()
        assert data["user"]["email"] == TEST_USER["email"]
        assert data["user"]["full_name"] == TEST_USER["full_name"]
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
        assert "hashed_password" not in data["user"]  # never expose this

    def test_register_duplicate_email(self):
        client.post("/api/v1/auth/register", json=TEST_USER)
        res = client.post("/api/v1/auth/register", json=TEST_USER)
        assert res.status_code == 400
        assert "already exists" in res.json()["detail"]

    def test_register_weak_password(self):
        res = client.post("/api/v1/auth/register", json={
            **TEST_USER, "password": "weak"
        })
        assert res.status_code == 422  # validation error

    def test_register_password_no_number(self):
        res = client.post("/api/v1/auth/register", json={
            **TEST_USER, "password": "NoNumberHere"
        })
        assert res.status_code == 422

    def test_register_invalid_email(self):
        res = client.post("/api/v1/auth/register", json={
            **TEST_USER, "email": "not-an-email"
        })
        assert res.status_code == 422


class TestLogin:
    def setup_method(self):
        client.post("/api/v1/auth/register", json=TEST_USER)

    def test_login_success(self):
        res = client.post("/api/v1/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        assert res.status_code == 200
        assert "access_token" in res.json()["tokens"]

    def test_login_wrong_password(self):
        res = client.post("/api/v1/auth/login", json={
            "email": TEST_USER["email"],
            "password": "WrongPass123"
        })
        assert res.status_code == 401

    def test_login_wrong_email(self):
        res = client.post("/api/v1/auth/login", json={
            "email": "nobody@finsight.lk",
            "password": TEST_USER["password"]
        })
        assert res.status_code == 401


class TestProtectedRoutes:
    def get_token(self):
        client.post("/api/v1/auth/register", json=TEST_USER)
        res = client.post("/api/v1/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        return res.json()["tokens"]["access_token"]

    def test_get_me_authenticated(self):
        token = self.get_token()
        res = client.get("/api/v1/auth/me",
                         headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json()["email"] == TEST_USER["email"]

    def test_get_me_no_token(self):
        res = client.get("/api/v1/auth/me")
        assert res.status_code == 401

    def test_get_me_invalid_token(self):
        res = client.get("/api/v1/auth/me",
                         headers={"Authorization": "Bearer fake.token.here"})
        assert res.status_code == 401

    def test_refresh_token(self):
        client.post("/api/v1/auth/register", json=TEST_USER)
        login_res = client.post("/api/v1/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        refresh_token = login_res.json()["tokens"]["refresh_token"]
        res = client.post("/api/v1/auth/refresh",
                          json={"refresh_token": refresh_token})
        assert res.status_code == 200
        assert "access_token" in res.json()
