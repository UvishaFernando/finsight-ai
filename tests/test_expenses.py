"""
Expense endpoint integration tests.
Uses SQLite in-memory DB — no PostgreSQL needed to run tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from app.main import app
from app.db.base import Base, get_db

SQLITE_URL = "sqlite:///./test_expenses.db"
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
    "email": "expense_test@finsight.lk",
    "full_name": "Test User",
    "password": "TestPass123"
}


def get_auth_headers():
    client.post("/api/v1/auth/register", json=TEST_USER)
    res = client.post("/api/v1/auth/login", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    })
    token = res.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestCreateExpense:
    def test_create_with_auto_categorization(self):
        headers = get_auth_headers()
        res = client.post("/api/v1/expenses/", headers=headers, json={
            "amount": 2500.00,
            "description": "Keells supermarket weekly shopping",
            "transaction_date": str(date.today()),
        })
        assert res.status_code == 201
        data = res.json()
        assert data["category"] == "supermarket"
        assert data["auto_categorized"] is True
        assert data["categorization_reason"] is not None
        assert float(data["amount"]) == 2500.00

    def test_create_with_manual_category(self):
        headers = get_auth_headers()
        res = client.post("/api/v1/expenses/", headers=headers, json={
            "amount": 1200.00,
            "description": "Monthly expenses",
            "category": "food_groceries",
            "transaction_type": "expense",
            "transaction_date": str(date.today()),
        })
        assert res.status_code == 201
        data = res.json()
        assert data["category"] == "food_groceries"
        assert data["auto_categorized"] is False

    def test_create_salary_income(self):
        headers = get_auth_headers()
        res = client.post("/api/v1/expenses/", headers=headers, json={
            "amount": 85000.00,
            "description": "Monthly salary April",
            "transaction_date": str(date.today()),
        })
        assert res.status_code == 201
        data = res.json()
        assert data["category"] == "salary"
        assert data["transaction_type"] == "income"

    def test_create_ceb_bill(self):
        headers = get_auth_headers()
        res = client.post("/api/v1/expenses/", headers=headers, json={
            "amount": 4800.00,
            "description": "CEB electricity bill March",
            "transaction_date": str(date.today()),
        })
        assert res.status_code == 201
        assert res.json()["category"] == "electricity_ceb"

    def test_create_negative_amount_fails(self):
        headers = get_auth_headers()
        res = client.post("/api/v1/expenses/", headers=headers, json={
            "amount": -100.00,
            "description": "Test",
            "transaction_date": str(date.today()),
        })
        assert res.status_code == 422

    def test_create_zero_amount_fails(self):
        headers = get_auth_headers()
        res = client.post("/api/v1/expenses/", headers=headers, json={
            "amount": 0,
            "description": "Test",
            "transaction_date": str(date.today()),
        })
        assert res.status_code == 422

    def test_unauthenticated_create_fails(self):
        res = client.post("/api/v1/expenses/", json={
            "amount": 100.00,
            "description": "Test",
            "transaction_date": str(date.today()),
        })
        assert res.status_code == 401


class TestListExpenses:
    def _create_expense(self, headers, desc, amount, category=None):
        payload = {
            "amount": amount,
            "description": desc,
            "transaction_date": str(date.today()),
        }
        if category:
            payload["category"] = category
            payload["transaction_type"] = "expense"
        client.post("/api/v1/expenses/", headers=headers, json=payload)

    def test_list_returns_all(self):
        headers = get_auth_headers()
        self._create_expense(headers, "CEB bill", 3000)
        self._create_expense(headers, "Keells shopping", 2000)
        res = client.get("/api/v1/expenses/", headers=headers)
        assert res.status_code == 200
        assert res.json()["total"] == 2

    def test_list_filter_by_category(self):
        headers = get_auth_headers()
        self._create_expense(headers, "CEB bill", 3000)
        self._create_expense(headers, "Keells shopping", 2000)
        res = client.get(
            "/api/v1/expenses/?category=electricity_ceb", headers=headers
        )
        assert res.status_code == 200
        assert res.json()["total"] == 1

    def test_list_pagination(self):
        headers = get_auth_headers()
        for i in range(5):
            self._create_expense(headers, f"Expense {i}", 100 + i)
        res = client.get("/api/v1/expenses/?page=1&page_size=2", headers=headers)
        data = res.json()
        assert len(data["expenses"]) == 2
        assert data["total"] == 5
        assert data["total_pages"] == 3

    def test_users_cannot_see_each_others_expenses(self):
        headers1 = get_auth_headers()
        client.post("/api/v1/auth/register", json={
            "email": "other@finsight.lk",
            "full_name": "Other User",
            "password": "OtherPass123"
        })
        res2 = client.post("/api/v1/auth/login", json={
            "email": "other@finsight.lk",
            "password": "OtherPass123"
        })
        headers2 = {"Authorization": f"Bearer {res2.json()['tokens']['access_token']}"}

        self._create_expense(headers1, "CEB bill user 1", 3000)
        res = client.get("/api/v1/expenses/", headers=headers2)
        assert res.json()["total"] == 0  # user 2 sees nothing


class TestUpdateDeleteExpense:
    def test_update_amount(self):
        headers = get_auth_headers()
        create_res = client.post("/api/v1/expenses/", headers=headers, json={
            "amount": 1000.00,
            "description": "CEB bill",
            "transaction_date": str(date.today()),
        })
        expense_id = create_res.json()["id"]
        res = client.put(f"/api/v1/expenses/{expense_id}", headers=headers,
                         json={"amount": 1500.00})
        assert res.status_code == 200
        assert float(res.json()["amount"]) == 1500.00

    def test_delete_expense(self):
        headers = get_auth_headers()
        create_res = client.post("/api/v1/expenses/", headers=headers, json={
            "amount": 500.00,
            "description": "Test delete",
            "transaction_date": str(date.today()),
        })
        expense_id = create_res.json()["id"]
        res = client.delete(f"/api/v1/expenses/{expense_id}", headers=headers)
        assert res.status_code == 200
        # Confirm it's gone
        get_res = client.get(f"/api/v1/expenses/{expense_id}", headers=headers)
        assert get_res.status_code == 404

    def test_cannot_delete_others_expense(self):
        headers1 = get_auth_headers()
        create_res = client.post("/api/v1/expenses/", headers=headers1, json={
            "amount": 500.00,
            "description": "My expense",
            "transaction_date": str(date.today()),
        })
        expense_id = create_res.json()["id"]

        client.post("/api/v1/auth/register", json={
            "email": "attacker@finsight.lk",
            "full_name": "Attacker",
            "password": "AttackPass123"
        })
        res2 = client.post("/api/v1/auth/login", json={
            "email": "attacker@finsight.lk",
            "password": "AttackPass123"
        })
        headers2 = {"Authorization": f"Bearer {res2.json()['tokens']['access_token']}"}
        res = client.delete(f"/api/v1/expenses/{expense_id}", headers=headers2)
        assert res.status_code == 404  # attacker sees 404, not 403 (no info leak)


class TestAIPreview:
    def test_preview_keells(self):
        headers = get_auth_headers()
        res = client.post(
            "/api/v1/expenses/ai/preview-category?description=Keells+supermarket",
            headers=headers
        )
        assert res.status_code == 200
        data = res.json()
        assert data["suggested_category"] == "supermarket"
        assert data["confidence"] >= 0.95
        assert data["matched_keyword"]
        assert data["reasoning"]

    def test_preview_ceb(self):
        headers = get_auth_headers()
        res = client.post(
            "/api/v1/expenses/ai/preview-category?description=CEB+electricity+bill",
            headers=headers
        )
        assert res.json()["suggested_category"] == "electricity_ceb"
