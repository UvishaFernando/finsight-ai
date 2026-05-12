"""
Tests for the Sri Lanka auto-categorization AI engine.
Run with: pytest tests/test_categorizer.py -v
"""
import pytest
from app.services.categorizer import categorize, categorize_batch
from app.models.expense import ExpenseCategory, TransactionType


class TestCategorizerSriLankaKeywords:
    """Test that Sri Lanka-specific businesses are recognized correctly."""

    def test_keells(self):
        r = categorize("Keells supermarket weekly shopping")
        assert r.category == ExpenseCategory.supermarket
        assert r.confidence >= 0.95

    def test_cargills(self):
        r = categorize("Cargills food city groceries")
        assert r.category == ExpenseCategory.supermarket

    def test_ceb_electricity(self):
        r = categorize("CEB electricity bill March")
        assert r.category == ExpenseCategory.electricity_ceb
        assert r.confidence >= 0.99

    def test_dialog_reload(self):
        r = categorize("Dialog reload 200")
        assert r.category == ExpenseCategory.mobile_dialog
        assert r.confidence >= 0.99

    def test_mobitel(self):
        r = categorize("Mobitel data pack 1GB")
        assert r.category == ExpenseCategory.mobile_mobitel

    def test_pickme(self):
        r = categorize("PickMe to Colombo fort")
        assert r.category == ExpenseCategory.transport_rideshare
        assert r.confidence >= 0.97

    def test_ceypetco_fuel(self):
        r = categorize("Filled petrol at CEYPETCO station")
        assert r.category == ExpenseCategory.transport_fuel

    def test_pola(self):
        r = categorize("Pola Saturday vegetables and fruits")
        assert r.category == ExpenseCategory.pola_market

    def test_nwsdb_water(self):
        r = categorize("NWSDB water bill April")
        assert r.category == ExpenseCategory.water_nwsdb

    def test_salary_income(self):
        r = categorize("Monthly salary April")
        assert r.category == ExpenseCategory.salary
        assert r.transaction_type == TransactionType.income

    def test_hospital(self):
        r = categorize("Nawaloka hospital consultation")
        assert r.category == ExpenseCategory.healthcare

    def test_rent(self):
        r = categorize("House rent May Colombo")
        assert r.category == ExpenseCategory.rent

    def test_bus_fare(self):
        r = categorize("Bus fare to Kandy")
        assert r.category == ExpenseCategory.transport_bus

    def test_tuk(self):
        r = categorize("Tuk tuk to market")
        assert r.category == ExpenseCategory.transport_tuk

    def test_school_tuition(self):
        r = categorize("School tuition fee May")
        assert r.category == ExpenseCategory.education

    def test_netflix(self):
        r = categorize("Netflix monthly subscription")
        assert r.category == ExpenseCategory.entertainment

    def test_kottu_restaurant(self):
        r = categorize("Kottu and rice and curry dinner")
        assert r.category == ExpenseCategory.restaurants

    def test_freelance_upwork(self):
        r = categorize("Upwork client payment project done")
        assert r.category == ExpenseCategory.freelance
        assert r.transaction_type == TransactionType.income


class TestCategorizerEdgeCases:
    """Test edge cases and fallbacks."""

    def test_unknown_description_defaults_expense(self):
        r = categorize("Random unknown thing xyz")
        assert r.category == ExpenseCategory.other_expense
        assert r.confidence <= 0.35

    def test_income_hint_fallback(self):
        r = categorize("Received payment from client")
        assert r.transaction_type == TransactionType.income

    def test_case_insensitive(self):
        r1 = categorize("KEELLS SUPERMARKET")
        r2 = categorize("keells supermarket")
        r3 = categorize("Keells Supermarket")
        assert r1.category == r2.category == r3.category

    def test_mixed_case_ceb(self):
        r = categorize("CEB Bill")
        assert r.category == ExpenseCategory.electricity_ceb

    def test_extra_whitespace(self):
        r = categorize("  Dialog   reload  ")
        assert r.category == ExpenseCategory.mobile_dialog

    def test_returns_reasoning(self):
        r = categorize("Keells weekly shop")
        assert r.reasoning
        assert len(r.reasoning) > 10

    def test_returns_matched_keyword(self):
        r = categorize("CEB electricity bill")
        assert r.matched_keyword
        assert "ceb" in r.matched_keyword.lower()


class TestCategorizerSpecificity:
    """More specific matches should beat less specific ones."""

    def test_pickme_beats_generic_transport(self):
        r = categorize("PickMe bus ride Colombo")
        # PickMe (rideshare) should beat bus (transport_bus)
        assert r.category == ExpenseCategory.transport_rideshare

    def test_supermarket_beats_food(self):
        r = categorize("Keells food shopping")
        assert r.category == ExpenseCategory.supermarket

    def test_dialog_broadband_is_internet(self):
        r = categorize("Dialog broadband monthly bill")
        assert r.category == ExpenseCategory.internet


class TestBatchCategorization:
    def test_batch_returns_correct_count(self):
        descriptions = [
            "Keells shopping",
            "CEB bill",
            "Dialog reload",
            "Monthly salary",
            "Unknown thing",
        ]
        results = categorize_batch(descriptions)
        assert len(results) == 5

    def test_batch_correct_categories(self):
        descriptions = ["Keells", "CEB", "Dialog"]
        results = categorize_batch(descriptions)
        assert results[0].category == ExpenseCategory.supermarket
        assert results[1].category == ExpenseCategory.electricity_ceb
        assert results[2].category == ExpenseCategory.mobile_dialog
