#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Database migration helper."""

import os
import sys

import dotenv
from flask_migrate import upgrade

# Add the project root to Python path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables.
dotenv.load_dotenv()

# Import Flask app.
from app.http.app import app


def migrate_database():
    """Run database migrations."""
    with app.app_context():
        try:
            print("Starting database migration...")
            upgrade(directory="internal/migration")
            print("Database migration completed successfully.")
        except Exception as e:
            print(f"Database migration failed: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    migrate_database()
