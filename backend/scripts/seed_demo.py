#!/usr/bin/env python3
"""
Seed Demo Data Script for IDKit

Creates demo users and sample data for preview/testing.
Uses raw SQL to avoid full model graph issues.
"""

import asyncio
import sys
from datetime import datetime, timezone
from uuid import uuid4

sys.path.insert(0, ".")

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


# Demo accounts configuration
DEMO_ACCOUNTS = [
    {
        "id": str(uuid4()),
        "email": "admin@idkit.io",
        "full_name": "Admin User",
        "is_active": True,
        "is_verified": True,
        "subscription_tier": "enterprise",
        "username": "admin",
        "display_name": "Admin User",
        "bio": "IDKit Administrator",
        "role": "admin",
    },
    {
        "id": str(uuid4()),
        "email": "creator@idkit.io",
        "full_name": "Demo Creator",
        "is_active": True,
        "is_verified": True,
        "subscription_tier": "pro",
        "username": "democreator",
        "display_name": "Demo Creator",
        "bio": "Professional content creator with 500K+ followers. Tech, lifestyle, and travel content.",
        "role": "creator",
    },
    {
        "id": str(uuid4()),
        "email": "test@idkit.io",
        "full_name": "Test User",
        "is_active": True,
        "is_verified": False,
        "subscription_tier": "free",
        "username": "testuser",
        "display_name": "Test User",
        "bio": "Test account for development",
        "role": "user",
    },
]


async def seed_users_raw(engine):
    """Seed demo users using raw SQL."""
    print("🌱 Seeding demo users...")
    
    now = datetime.now(timezone.utc).isoformat()
    
    async with engine.begin() as conn:
        # Create users table if not exists
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT,
                is_active INTEGER DEFAULT 1,
                is_verified INTEGER DEFAULT 0,
                subscription_tier TEXT DEFAULT 'free',
                oauth_provider TEXT,
                oauth_provider_id TEXT,
                avatar_url TEXT,
                last_login_at TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """))
        
        # Create user_profiles table if not exists
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id TEXT PRIMARY KEY,
                user_id TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                bio TEXT,
                avatar_url TEXT,
                cover_image_url TEXT,
                website_url TEXT,
                follower_count INTEGER DEFAULT 0,
                following_count INTEGER DEFAULT 0,
                post_count INTEGER DEFAULT 0,
                is_verified INTEGER DEFAULT 0,
                niche_tags TEXT DEFAULT '[]',
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        
        for account in DEMO_ACCOUNTS:
            # Check if user exists
            result = await conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": account["email"]}
            )
            existing = result.fetchone()
            
            if existing:
                print(f"   ⏭️  User {account['email']} already exists")
                continue
            
            # Insert user
            await conn.execute(
                text("""
                    INSERT INTO users (id, email, full_name, is_active, is_verified, subscription_tier, created_at, updated_at)
                    VALUES (:id, :email, :full_name, :is_active, :is_verified, :subscription_tier, :created_at, :updated_at)
                """),
                {
                    "id": account["id"],
                    "email": account["email"],
                    "full_name": account["full_name"],
                    "is_active": 1 if account["is_active"] else 0,
                    "is_verified": 1 if account["is_verified"] else 0,
                    "subscription_tier": account["subscription_tier"],
                    "created_at": now,
                    "updated_at": now,
                }
            )
            
            # Insert profile
            profile_id = str(uuid4())
            follower_count = 0 if account["role"] == "user" else 50000
            
            await conn.execute(
                text("""
                    INSERT INTO user_profiles (id, user_id, username, display_name, bio, follower_count, following_count, post_count, is_verified, created_at, updated_at)
                    VALUES (:id, :user_id, :username, :display_name, :bio, :follower_count, :following_count, :post_count, :is_verified, :created_at, :updated_at)
                """),
                {
                    "id": profile_id,
                    "user_id": account["id"],
                    "username": account["username"],
                    "display_name": account["display_name"],
                    "bio": account.get("bio", ""),
                    "follower_count": follower_count,
                    "following_count": 100,
                    "post_count": 0,
                    "is_verified": 1 if account["is_verified"] else 0,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            
            print(f"   ✅ Created user: {account['email']} ({account['role']})")
    
    print("✅ Demo users seeded successfully!")


async def main():
    """Main entry point."""
    import os
    
    # Get database URL from environment or use default
    database_url = os.getenv(
        "DATABASE_URL", 
        "sqlite+aiosqlite:///./idkit_preview.db"
    )
    
    print(f"📊 Database: {database_url}")
    print("=" * 50)
    
    # Create engine
    engine = create_async_engine(database_url, echo=False)
    
    await seed_users_raw(engine)
    
    await engine.dispose()
    
    print("")
    print("=" * 50)
    print("🎉 Seed completed!")
    print("")
    print("Demo Accounts:")
    print("  📧 admin@idkit.io    (Enterprise Admin)")
    print("  📧 creator@idkit.io  (Pro Creator)")
    print("  📧 test@idkit.io     (Free User)")
    print("")
    print("Note: Login uses OAuth (Google) - no passwords")


if __name__ == "__main__":
    asyncio.run(main())
