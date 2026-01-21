from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from routers.auth import get_password_hash

def init_db():
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("Creating default admin user...")
            admin_user = User(
                username="admin",
                email="admin@example.com",  # Default email
                password_hash=get_password_hash("admin123"),
                first_name="System",
                last_name="Administrator",
                phone_number=None,
                role="admin",
                is_active=True,
                can_take_duty=False  # Admin doesn't take duty by default
            )
            db.add(admin_user)
            db.commit()
            print("Default admin created: admin / admin123")
        else:
            print("Admin user already exists.")
    except Exception as e:
        print(f"Error initializing DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
