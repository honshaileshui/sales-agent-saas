"""
Setup Script - Fix User Password
================================
Run this once to properly set up the test user with a hashed password.
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_user_password():
    print("=" * 50)
    print("Setting Up User Password")
    print("=" * 50)
    
    # First, let's try to import and test
    try:
        from passlib.context import CryptContext
        print("✅ passlib imported successfully")
    except ImportError:
        print("❌ passlib not found. Installing...")
        os.system("pip install passlib[bcrypt]")
        from passlib.context import CryptContext
    
    try:
        from database import get_db_cursor, test_connection
        print("✅ database module imported")
    except ImportError as e:
        print(f"❌ Could not import database: {e}")
        return
    
    # Test database connection
    if not test_connection():
        print("❌ Database connection failed!")
        return
    
    print("✅ Database connected")
    
    # Create password hash
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    password = "password123"
    hashed = pwd_context.hash(password)
    
    print(f"\n🔐 Generated hash for '{password}':")
    print(f"   {hashed[:50]}...")
    
    # Update the user in database
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET password_hash = %s 
                WHERE email = 'shailesh@test.com'
                RETURNING email, full_name
            """, (hashed,))
            result = cursor.fetchone()
            
            if result:
                print(f"\n✅ Password updated for: {result['full_name']} ({result['email']})")
                print(f"\n📋 Login Credentials:")
                print(f"   Email: shailesh@test.com")
                print(f"   Password: password123")
            else:
                print("❌ User not found. Creating new user...")
                
                cursor.execute("""
                    INSERT INTO users (email, password_hash, full_name, company_name, plan_type)
                    VALUES ('shailesh@test.com', %s, 'Shailesh Hon', 'SalesAgent AI', 'pro')
                    ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash
                    RETURNING email, full_name
                """, (hashed,))
                result = cursor.fetchone()
                print(f"✅ User created/updated: {result['full_name']}")
                
    except Exception as e:
        print(f"❌ Error updating password: {e}")
        return
    
    print("\n" + "=" * 50)
    print("✅ Setup Complete!")
    print("=" * 50)
    print("\nNow run: uvicorn api.main:app --reload --port 8000")
    print("Then go to: http://localhost:8000/docs")
    print("\nLogin with:")
    print("  Email: shailesh@test.com")
    print("  Password: password123")


if __name__ == "__main__":
    setup_user_password()