"""Seed default phishing templates."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.models import PhishingTemplate
from backend.data.phishing_templates import PHISHING_TEMPLATES


def seed_phishing_templates(db: Session):
    """Seed default phishing templates."""
    print("Seeding phishing templates...")
    
    # Check if templates already exist
    existing_count = db.query(PhishingTemplate).count()
    if existing_count > 0:
        print(f"Found {existing_count} existing templates. Skipping seed.")
        return
    
    # Add default templates
    for template_data in PHISHING_TEMPLATES:
        template = PhishingTemplate(**template_data)
        db.add(template)
    
    db.commit()
    print(f"Added {len(PHISHING_TEMPLATES)} phishing templates.")


def main():
    """Main function."""
    db = SessionLocal()
    try:
        seed_phishing_templates(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()