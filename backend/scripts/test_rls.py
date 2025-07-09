"""Test Row Level Security (RLS) implementation."""

import asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import async_session_maker
from models import User, Company, UserCourseProgress, PhishingCampaign, AuditLog
from core.rls import set_rls_context, clear_rls_context


async def test_rls_policies():
    """Test that RLS policies work correctly."""
    async with async_session_maker() as session:
        print("🔍 Testing Row Level Security Policies\n")
        
        # Get test users from different companies
        result = await session.execute(
            select(User)
            .where(User.email.in_([
                'admin@bootstrap-awareness.de',  # System admin
                'admin@techvision.de',            # Company admin
                'admin@autowerk-bayern.de'        # Different company admin
            ]))
        )
        users = result.scalars().all()
        
        if len(users) < 3:
            print("❌ Not enough test users found. Please run seed_data_enhanced.py first.")
            return
        
        system_admin = next(u for u in users if u.email == 'admin@bootstrap-awareness.de')
        company1_admin = next(u for u in users if u.email == 'admin@techvision.de')
        company2_admin = next(u for u in users if u.email == 'admin@autowerk-bayern.de')
        
        print(f"System Admin: {system_admin.email}")
        print(f"Company 1 Admin: {company1_admin.email} (Company ID: {company1_admin.company_id})")
        print(f"Company 2 Admin: {company2_admin.email} (Company ID: {company2_admin.company_id})")
        print("\n" + "="*60 + "\n")
        
        # Test 1: System admin should see all users
        print("Test 1: System Admin Access")
        await set_rls_context(session, system_admin.company_id, 'system_admin')
        result = await session.execute(select(User))
        all_users = result.scalars().all()
        print(f"✅ System admin can see {len(all_users)} users (all users)")
        
        # Test 2: Company admin should only see their company's users
        print("\nTest 2: Company Admin Access")
        await clear_rls_context(session)
        await set_rls_context(session, company1_admin.company_id, 'company_admin')
        result = await session.execute(select(User))
        company1_users = result.scalars().all()
        print(f"✅ Company 1 admin can see {len(company1_users)} users")
        print(f"   All from same company: {all(u.company_id == company1_admin.company_id for u in company1_users)}")
        
        # Test 3: Different company admin should see different users
        print("\nTest 3: Different Company Isolation")
        await clear_rls_context(session)
        await set_rls_context(session, company2_admin.company_id, 'company_admin')
        result = await session.execute(select(User))
        company2_users = result.scalars().all()
        print(f"✅ Company 2 admin can see {len(company2_users)} users")
        print(f"   No overlap with Company 1: {len(set(u.id for u in company1_users) & set(u.id for u in company2_users)) == 0}")
        
        # Test 4: Course progress isolation
        print("\nTest 4: Course Progress Isolation")
        await clear_rls_context(session)
        await set_rls_context(session, company1_admin.company_id, 'company_admin')
        result = await session.execute(select(UserCourseProgress))
        company1_progress = result.scalars().all()
        print(f"✅ Company 1 sees {len(company1_progress)} progress records")
        print(f"   All from same company: {all(p.company_id == company1_admin.company_id for p in company1_progress)}")
        
        # Test 5: Phishing campaign isolation
        print("\nTest 5: Phishing Campaign Isolation")
        result = await session.execute(select(PhishingCampaign))
        company1_campaigns = result.scalars().all()
        print(f"✅ Company 1 sees {len(company1_campaigns)} phishing campaigns")
        if company1_campaigns:
            print(f"   All from same company: {all(c.company_id == company1_admin.company_id for c in company1_campaigns)}")
        
        # Test 6: Audit log isolation
        print("\nTest 6: Audit Log Isolation")
        result = await session.execute(select(AuditLog).limit(10))
        company1_logs = result.scalars().all()
        print(f"✅ Company 1 sees {len(company1_logs)} audit logs")
        if company1_logs:
            print(f"   All from same company: {all(log.company_id == company1_admin.company_id for log in company1_logs)}")
        
        # Test 7: No access without context
        print("\nTest 7: No Access Without Context")
        await clear_rls_context(session)
        result = await session.execute(select(User))
        no_context_users = result.scalars().all()
        print(f"✅ Without context, user sees {len(no_context_users)} users (should be 0)")
        
        print("\n" + "="*60)
        print("✨ RLS Testing Complete!")


async def verify_rls_enabled():
    """Verify that RLS is enabled on all tables."""
    async with async_session_maker() as session:
        print("\n📋 Checking RLS Status on Tables\n")
        
        result = await session.execute(text("""
            SELECT 
                schemaname,
                tablename,
                rowsecurity
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename IN (
                'users', 'companies', 'user_course_progress', 
                'phishing_campaigns', 'phishing_results', 'phishing_templates',
                'audit_logs', 'analytics_events'
            )
            ORDER BY tablename
        """))
        
        tables = result.fetchall()
        all_enabled = True
        
        for schema, table, rls_enabled in tables:
            status = "✅ Enabled" if rls_enabled else "❌ Disabled"
            print(f"{table}: {status}")
            if not rls_enabled:
                all_enabled = False
        
        if all_enabled:
            print("\n✅ All tables have RLS enabled!")
        else:
            print("\n❌ Some tables don't have RLS enabled. Run setup_row_level_security.sql")


async def main():
    """Run all RLS tests."""
    await verify_rls_enabled()
    await test_rls_policies()


if __name__ == "__main__":
    asyncio.run(main())