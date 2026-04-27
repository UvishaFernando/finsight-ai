from __future__ import annotations


DEFAULT_CATEGORY = "other"


def suggest_category(text: str) -> str:
    """
    Very simple rule-based categorizer.
    We keep it deterministic and easy to extend.
    """
    t = (text or "").strip().lower()
    if not t:
        return DEFAULT_CATEGORY

    rules: list[tuple[str, set[str]]] = [
        ("food", {"rice", "dhal", "kottu", "roti", "milk", "tea", "lunch", "dinner", "breakfast", "pola"}),
        ("transport", {"uber", "pickme", "pick me", "bus", "train", "tuk", "threewheel", "three wheel", "petrol"}),
        ("bills", {"electricity", "ceb", "water", "wifi", "internet", "dialog", "mobitel", "hutch"}),
        ("health", {"hospital", "pharmacy", "medicine", "doctor", "clinic"}),
        ("education", {"course", "tuition", "class", "exam", "book"}),
    ]

    for category, keywords in rules:
        if any(k in t for k in keywords):
            return category

    return DEFAULT_CATEGORY
