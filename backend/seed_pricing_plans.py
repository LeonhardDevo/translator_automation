"""
Script to seed the database with initial pricing plans
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.database import get_session
from app.models.pricing_models import PricingPlan
from datetime import datetime

def seed_pricing_plans():
    with get_session() as session:
        # Check if plans already exist
        existing_plans = session.query(PricingPlan).all()
        if existing_plans:
            print("Pricing plans already exist, skipping seeding.")
            return
        
        # Create the four required plans
        plans = [
            PricingPlan(
                name="Free Trial",
                max_translation_count=10,  # Small amount for trial
                price_for_max_translation_per_counts=0,
                description="1-day free trial with limited translations",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            PricingPlan(
                name="Basic (100 images)",
                max_translation_count=100,
                price_for_max_translation_per_counts=999,  # $9.99 in cents
                description="Basic plan with standard translation allowance",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            PricingPlan(
                name="Professional (1000 images)",
                max_translation_count=1000,
                price_for_max_translation_per_counts=2999,  # $29.99 in cents
                description="Professional plan with higher translation limits",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            PricingPlan(
                name="Enterprise (10000 images)",
                max_translation_count=10000,
                price_for_max_translation_per_counts=9999,  # $99.99 in cents
                description="Enterprise plan with highest translation limits",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        for plan in plans:
            session.add(plan)
        
        print("Pricing plans seeded successfully!")

if __name__ == "__main__":
    seed_pricing_plans()