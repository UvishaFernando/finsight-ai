import re
from dataclasses import dataclass
from typing import Optional
from app.models.expense import ExpenseCategory, TransactionType


@dataclass
class CategorizationResult:
    category: ExpenseCategory
    transaction_type: TransactionType
    confidence: float          
    matched_keyword: str       
    reasoning: str            


KEYWORD_MAP: list[tuple[ExpenseCategory, TransactionType, list[str], float]] = [

    # ── INCOME ───────────────────────────────────────────────────────────────
    (ExpenseCategory.salary, TransactionType.income, [
        "salary", "salery", "monthly pay", "payslip", "wage"
    ], 0.97),

    (ExpenseCategory.freelance, TransactionType.income, [
        "freelance", "upwork", "fiverr", "client payment", "invoice paid",
        "project payment", "contract pay",
    ], 0.95),

    (ExpenseCategory.business_income, TransactionType.income, [
        "sales income", "shop income", "business", "revenue", "profit",
    ], 0.90),

    # ── UTILITIES ─────────────────────────────────────────────────────────────
    (ExpenseCategory.electricity_ceb, TransactionType.expense, [
        "ceb", "ceylon electricity", "electricity bill", "light bill",
        "current bill", "power bill",
    ], 0.99),

    (ExpenseCategory.water_nwsdb, TransactionType.expense, [
        "nwsdb", "water board", "water bill", "wasa",
    ], 0.99),

    # ── MOBILE / PHONE ────────────────────────────────────────────────────────
    (ExpenseCategory.internet, TransactionType.expense, [
        "slt", "dialog broadband", "hutch", "mobitel broadband",
        "wifi bill", "internet bill", "broadband", "fiber",
    ], 0.995),

    (ExpenseCategory.mobile_dialog, TransactionType.expense, [
        "dialog", "dialog axiata", "dialog reload", "dialog topup",
        "dialog recharge",
    ], 0.99),

    (ExpenseCategory.mobile_mobitel, TransactionType.expense, [
        "mobitel", "mobitel reload", "mobitel topup", "mobitel recharge",
        "mobitel data",
    ], 0.99),

    # ── TRANSPORT ─────────────────────────────────────────────────────────────
    (ExpenseCategory.transport_rideshare, TransactionType.expense, [
        "pickme", "pick me", "uber", "bolt", "rideshare",
        "taxi app", "cab booking",
    ], 0.98),

    (ExpenseCategory.transport_fuel, TransactionType.expense, [
        "ceypetco", "fuel", "petrol", "diesel", "filling station",
        "gas station", "cpc fuel", "lanka ioc",
    ], 0.98),

    (ExpenseCategory.transport_tuk, TransactionType.expense, [
        "tuk", "three wheeler", "trishaw", "tuk tuk", "tuktuk",
        "three-wheeler",
    ], 0.95),

    (ExpenseCategory.transport_bus, TransactionType.expense, [
        "bus fare", "bus ticket", "ctb", "sltb", "private bus",
        "bus pass", "bus", "route ",
    ], 0.90),

    # ── SUPERMARKETS ──────────────────────────────────────────────────────────
    (ExpenseCategory.supermarket, TransactionType.expense, [
        "keells", "keels", "cargills", "cargill", "arpico", "laugfs",
        "spar", "food city", "supermarket", "grocery store",
        "supermart", "mall",
    ], 0.97),

    # ── POLA / LOCAL MARKET ───────────────────────────────────────────────────
    (ExpenseCategory.pola_market, TransactionType.expense, [
        "pola", "market", "weekly market", "fair", "bazaar",
        "economic centre", "manning market", "dambulla market",
        "pettah market",
    ], 0.93),

    # ── FOOD & RESTAURANTS ────────────────────────────────────────────────────
    (ExpenseCategory.restaurants, TransactionType.expense, [
        "restaurant", "cafe", "coffee", "kfc", "mcdonalds", "burger king",
        "pizza", "subway", "chinese", "hotel meal", "dinner", "lunch out",
        "kottu", "rice and curry", "biriyani", "chinese restaurant",
    ], 0.92),

    (ExpenseCategory.street_food, TransactionType.expense, [
        "wade", "isso wade", "kottu street", "street food", "kade",
        "tea kade", "bakery", "roti", "short eats", "pittu", "string hopper",
        "hopper", "appam", "samosa",
    ], 0.90),

    # General food (lower priority than specific)
    (ExpenseCategory.food_groceries, TransactionType.expense, [
        "grocery", "groceries", "vegetables", "veges", "rice", "dhal",
        "lentil", "coconut", "coconut oil", "milk", "egg", "chicken",
        "fish", "meat", "bread", "flour", "sugar", "salt", "onion",
        "tomato", "potato", "carrot", "beans", "fruit", "banana",
        "shopping", "food",
    ], 0.85),

    # ── HEALTHCARE ────────────────────────────────────────────────────────────
    (ExpenseCategory.healthcare, TransactionType.expense, [
        "hospital", "clinic", "doctor", "pharmacy", "medicine", "medical",
        "lab", "laboratory", "scan", "consultation", "channeling",
        "nawaloka", "asiri", "durdans", "colombo south",
        "dental", "eye test", "optician",
    ], 0.97),

    # ── EDUCATION ─────────────────────────────────────────────────────────────
    (ExpenseCategory.education, TransactionType.expense, [
        "school", "tuition", "class", "university", "college", "course",
        "exam fee", "books", "stationery", "school fee", "uva",
        "moratuwa", "colombo uni", "open university",
    ], 0.95),

    # ── RENT ──────────────────────────────────────────────────────────────────
    (ExpenseCategory.rent, TransactionType.expense, [
        "rent", "house rent", "room rent", "boarding", "landlord",
        "monthly rent", "housing",
    ], 0.98),

    # ── CLOTHING ──────────────────────────────────────────────────────────────
    (ExpenseCategory.clothing, TransactionType.expense, [
        "clothes", "clothing", "shirt", "dress", "shoes", "fashion",
        "h&m", "nolimit", "Cotton collection", "odel", "cool planet",
        "tailor", "alterations",
    ], 0.92),

    # ── ENTERTAINMENT ─────────────────────────────────────────────────────────
    (ExpenseCategory.entertainment, TransactionType.expense, [
        "netflix", "youtube premium", "spotify", "amazon prime",
        "movie", "cinema", "regal", "majestic", "liberty", "pvr",
        "game", "gaming", "playstation", "steam",
        "concert", "event", "ticket",
    ], 0.93),
]


def _clean_text(text: str) :
    """Normalize description for matching."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)   # remove punctuation
    text = re.sub(r"\s+", " ", text)        # collapse spaces
    return text


def _extract_amount_hint(text: str) :
    """Extract Rs. amount from description if present (for future use)."""
    match = re.search(r"(?:rs\.?|lkr)\s*(\d+(?:,\d+)*(?:\.\d+)?)", text.lower())
    if match:
        return float(match.group(1).replace(",", ""))
    return None


def categorize(description: str) :
    """
    Main entry point. Given a transaction description, returns the
    best matching category with confidence and reasoning.

    Examples:
        categorize("Keells supermarket groceries")
        → category=supermarket, confidence=0.97, matched="keells"

        categorize("Dialog reload 200")
        → category=mobile_dialog, confidence=0.99, matched="dialog reload"

        categorize("CEB electricity bill March")
        → category=electricity_ceb, confidence=0.99, matched="ceb"
    """
    cleaned = _clean_text(description)
    tokens = set(cleaned.split())

    best_match: Optional[CategorizationResult] = None
    
    for category, tx_type, keywords, base_confidence in KEYWORD_MAP:
        for keyword in keywords:
            kw_clean = _clean_text(keyword)
            # Check substring match (handles multi-word keywords)
            if kw_clean in cleaned:
                # Multi-word keywords are inherently specific — no penalty
                # Single-word keywords get a small penalty if not an exact word boundary
                is_multi_word = len(kw_clean.split()) > 1
                word_match = kw_clean in tokens
                confidence = base_confidence if (word_match or is_multi_word) else base_confidence - 0.05
                confidence = round(min(confidence, 1.0), 2)

                if best_match is None or confidence > best_match.confidence:
                    best_match = CategorizationResult(
                        category=category,
                        transaction_type=tx_type,
                        confidence=confidence,
                        matched_keyword=keyword,
                        reasoning=f"Description '{description}' matched keyword '{keyword}' → {category.value}",
                    )
                break  # one match per category rule is enough

    if best_match:
        return best_match

    # ── Fallback: no keyword matched ──────────────────────────────────────────
    # Use a simple heuristic: income keywords vs expense keywords
    income_hints = {"received", "income", "earned", "credit", "paid in"}
    if any(hint in cleaned for hint in income_hints):
        return CategorizationResult(
            category=ExpenseCategory.other_income,
            transaction_type=TransactionType.income,
            confidence=0.40,
            matched_keyword="[income hint]",
            reasoning="No specific match — detected income-related language",
        )

    return CategorizationResult(
        category=ExpenseCategory.other_expense,
        transaction_type=TransactionType.expense,
        confidence=0.30,
        matched_keyword="[no match]",
        reasoning="No keyword matched — defaulted to other_expense",
    )


def categorize_batch(descriptions: list[str]) :
    """Categorize multiple transactions at once."""
    return [categorize(d) for d in descriptions]


# ── Waste Detection ───────────────────────────────────────────────────────────

WASTEFUL_CATEGORIES = {
    ExpenseCategory.restaurants,
    ExpenseCategory.street_food,
    ExpenseCategory.entertainment,
    ExpenseCategory.clothing,
}

ESSENTIAL_CATEGORIES = {
    ExpenseCategory.food_groceries,
    ExpenseCategory.electricity_ceb,
    ExpenseCategory.water_nwsdb,
    ExpenseCategory.rent,
    ExpenseCategory.transport_bus,
    ExpenseCategory.healthcare,
    ExpenseCategory.education,
}


def is_potentially_wasteful(category: ExpenseCategory) :
    return category in WASTEFUL_CATEGORIES


def is_essential(category: ExpenseCategory) :
    return category in ESSENTIAL_CATEGORIES
