"""
Database migration script to update the schema with new tables and columns.
"""
from app import app, db
from models import Bank, Company, Employee, Check, CompanyClient

def migrate_database():
    """
    Migrate the database by recreating all tables.
    
    WARNING: This will delete all existing data. Use with caution in production.
    """
    with app.app_context():
        print("Starting database migration...")
        # Drop all tables
        db.drop_all()
        print("Dropped all tables")
        
        # Recreate all tables
        db.create_all()
        print("Recreated all tables")
        
        print("Database migration completed successfully")

if __name__ == "__main__":
    migrate_database()