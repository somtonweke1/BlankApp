"""
Database migration script for adding Inversion Mode tables.

Run this after adding the new models to create the necessary tables.
"""

from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from models import Base

load_dotenv()

def migrate():
    """Create all tables defined in models.py"""
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/mastery_machine")

    print(f"Connecting to database: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)

    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    print("✓ Migration complete!")
    print("\nNew tables created:")
    print("  - inversion_paragraphs")
    print("  - gaps")
    print("  - patches")
    print("\nYour database is now ready for Dialectical Learning Mode!")

if __name__ == "__main__":
    migrate()
