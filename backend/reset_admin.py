from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def reset_admin():
    db = SessionLocal()
    try:
        print("--- MANUELLER ADMIN RESET ---")
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        
        if admin:
            print("Admin user found. Updating password...")
            admin.password_hash = get_password_hash("admin123")
        else:
            print("Admin user NOT found. Creating new...")
            admin = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                role="admin"
            )
            db.add(admin)
        
        db.commit()
        print("SUCCESS: User 'admin' has password 'admin123'")
        
        # Verify immediately
        print("Verifying hash...")
        if pwd_context.verify("admin123", admin.password_hash):
            print("VERIFICATION OK: Hash matches 'admin123'")
        else:
            print("VERIFICATION FAILED: Hash does not match!")

    except Exception as e:
        print(f"Error resetting admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin()
