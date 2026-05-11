"""
Seed script — run once after DB creation to populate initial data.
Usage: python scripts/seed_db.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from app.db.base import SessionLocal, engine, Base
from app.models.price import MarketPrice
from app.models.user import User, UserRole
from app.core.security import hash_password

Base.metadata.create_all(bind=engine)

def seed_prices(db):
    prices = [
        {"item_name": "Rice (Samba, 1kg)",       "item_key": "rice_samba_1kg",    "category": "food",     "price_lkr": 210.00, "unit": "kg",     "source": "Keells/Cargills"},
        {"item_name": "Rice (Nadu, 1kg)",         "item_key": "rice_nadu_1kg",     "category": "food",     "price_lkr": 185.00, "unit": "kg",     "source": "Keells/Cargills"},
        {"item_name": "Dhal (1kg)",               "item_key": "dhal_1kg",          "category": "food",     "price_lkr": 320.00, "unit": "kg",     "source": "Keells/Cargills"},
        {"item_name": "Coconut Oil (750ml)",      "item_key": "coconut_oil_750ml", "category": "food",     "price_lkr": 680.00, "unit": "bottle", "source": "Keells/Cargills"},
        {"item_name": "Coconut (1 unit)",         "item_key": "coconut_1unit",     "category": "food",     "price_lkr": 85.00,  "unit": "unit",   "source": "Pola"},
        {"item_name": "Tomato (1kg)",             "item_key": "tomato_1kg",        "category": "food",     "price_lkr": 180.00, "unit": "kg",     "source": "Pola"},
        {"item_name": "Onion (1kg)",              "item_key": "onion_1kg",         "category": "food",     "price_lkr": 220.00, "unit": "kg",     "source": "Pola"},
        {"item_name": "Chicken (1kg)",            "item_key": "chicken_1kg",       "category": "food",     "price_lkr": 950.00, "unit": "kg",     "source": "Keells/Cargills"},
        {"item_name": "Eggs (10 pack)",           "item_key": "eggs_10pack",       "category": "food",     "price_lkr": 370.00, "unit": "pack",   "source": "Keells/Cargills"},
        {"item_name": "Milk powder (400g)",       "item_key": "milk_powder_400g",  "category": "food",     "price_lkr": 550.00, "unit": "pack",   "source": "Keells/Cargills"},
        {"item_name": "Petrol 92 Octane (1L)",   "item_key": "petrol_92_1l",      "category": "fuel",     "price_lkr": 317.00, "unit": "litre",  "source": "CEYPETCO"},
        {"item_name": "Petrol 95 Octane (1L)",   "item_key": "petrol_95_1l",      "category": "fuel",     "price_lkr": 338.00, "unit": "litre",  "source": "CEYPETCO"},
        {"item_name": "Auto Diesel (1L)",         "item_key": "diesel_1l",         "category": "fuel",     "price_lkr": 293.00, "unit": "litre",  "source": "CEYPETCO"},
        {"item_name": "CEB Tier 1 (0-30 units)", "item_key": "ceb_tier1",         "category": "utility",  "price_lkr": 8.00,   "unit": "kWh",    "source": "CEB"},
        {"item_name": "CEB Tier 2 (31-60 units)","item_key": "ceb_tier2",         "category": "utility",  "price_lkr": 35.00,  "unit": "kWh",    "source": "CEB"},
        {"item_name": "CEB Tier 3 (61-90 units)","item_key": "ceb_tier3",         "category": "utility",  "price_lkr": 54.00,  "unit": "kWh",    "source": "CEB"},
        {"item_name": "Bus fare (Colombo short)", "item_key": "bus_fare_short",    "category": "transport","price_lkr": 25.00,  "unit": "trip",   "source": "NTC"},
        {"item_name": "Tuk minimum fare",         "item_key": "tuk_minimum",       "category": "transport","price_lkr": 80.00,  "unit": "trip",   "source": "estimate"},
    ]
    today = date.today()
    added = 0
    for p in prices:
        existing = db.query(MarketPrice).filter(MarketPrice.item_key == p["item_key"]).first()
        if not existing:
            db.add(MarketPrice(**p, price_date=today))
            added += 1
    db.commit()
    print(f"Seeded {added} Sri Lanka market prices")

def seed_admin(db):
    existing = db.query(User).filter(User.email == "admin@finsight.lk").first()
    if not existing:
        admin = User(
            email="admin@finsight.lk",
            full_name="FinSight Admin",
            hashed_password=hash_password("Admin123!"),
            role=UserRole.admin,
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        db.commit()
        print("Admin user created: admin@finsight.lk / Admin123!")
    else:
        print("Admin user already exists")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_prices(db)
        seed_admin(db)
        print("\nDatabase seeded! Open http://localhost:8000/docs to test the API")
    finally:
        db.close()
