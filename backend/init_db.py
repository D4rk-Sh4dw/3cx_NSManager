from sqlalchemy import text
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import User
from routers.auth import get_password_hash


def migrate():
    """Bring an existing database up to date.

    The project has no migration tool, and create_all() only creates missing
    tables - it never alters existing ones. These statements are idempotent and
    safe to run on every start.
    """
    dialect = engine.dialect.name
    try:
        with engine.begin() as conn:
            if dialect == "postgresql":
                # SSO: subject of the identity provider, and password becomes optional
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS oidc_sub VARCHAR"))
                conn.execute(text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_oidc_sub ON users (oidc_sub)"
                ))
                conn.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL"))
            elif dialect == "sqlite":
                cols = [row[1] for row in conn.execute(text("PRAGMA table_info(users)"))]
                if cols and "oidc_sub" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN oidc_sub VARCHAR"))
                    conn.execute(text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_oidc_sub ON users (oidc_sub)"
                    ))
                # SQLite cannot drop NOT NULL; fresh databases get it right from create_all().
    except Exception as e:
        print(f"Error running migrations: {e}")


def init_db():
    migrate()
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
