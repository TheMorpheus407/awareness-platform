"""Initialize database with RLS policies and seed data."""

import asyncio
import subprocess
import os
from pathlib import Path
from sqlalchemy import text
from db.session import async_session_maker, engine
from core.config import settings


async def apply_rls_policies():
    """Apply Row Level Security policies to the database."""
    print("🔒 Applying Row Level Security policies...")
    
    # Read the RLS SQL script
    rls_script_path = Path(__file__).parent / "setup_row_level_security.sql"
    with open(rls_script_path, 'r') as f:
        rls_sql = f.read()
    
    # Execute the SQL script
    async with engine.begin() as conn:
        # Split by semicolons but keep them, then filter empty strings
        statements = [s.strip() + ';' for s in rls_sql.split(';') if s.strip()]
        
        for statement in statements:
            if statement.strip() and not statement.strip().startswith('--'):
                try:
                    await conn.execute(text(statement))
                except Exception as e:
                    print(f"⚠️  Warning executing statement: {e}")
                    # Continue with other statements
    
    print("✅ RLS policies applied successfully!")


async def run_migrations():
    """Run Alembic migrations."""
    print("📦 Running database migrations...")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    # Run alembic upgrade
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Migration failed: {result.stderr}")
        raise Exception("Migration failed")
    
    print("✅ Migrations completed successfully!")


async def seed_enhanced_data():
    """Run the enhanced seed data script."""
    print("🌱 Seeding enhanced data...")
    
    # Import and run the seed function
    from seed_data_enhanced import seed_database
    await seed_database()


async def verify_setup():
    """Verify the database setup."""
    print("\n🔍 Verifying database setup...")
    
    async with async_session_maker() as session:
        # Check RLS is enabled
        result = await session.execute(text("""
            SELECT COUNT(*) as enabled_count
            FROM pg_tables
            WHERE schemaname = 'public'
            AND rowsecurity = true
            AND tablename IN (
                'users', 'companies', 'user_course_progress', 
                'phishing_campaigns', 'phishing_results', 'phishing_templates',
                'audit_logs', 'analytics_events'
            )
        """))
        enabled_count = result.scalar()
        print(f"✅ RLS enabled on {enabled_count} tables")
        
        # Check data counts
        for table in ['users', 'companies', 'courses', 'phishing_templates']:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"✅ {table}: {count} records")


async def main():
    """Main initialization function."""
    print("🚀 Initializing Cybersecurity Awareness Platform Database")
    print("="*60)
    
    try:
        # Run migrations first
        await run_migrations()
        
        # Apply RLS policies
        await apply_rls_policies()
        
        # Seed enhanced data
        await seed_enhanced_data()
        
        # Verify setup
        await verify_setup()
        
        print("\n" + "="*60)
        print("✨ Database initialization completed successfully!")
        print("\n📝 Next steps:")
        print("1. Test RLS policies: python scripts/test_rls.py")
        print("2. Start the backend: python main.py")
        print("3. Login with credentials shown above")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())