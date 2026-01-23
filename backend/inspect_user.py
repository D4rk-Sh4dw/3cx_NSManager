from sqlalchemy import create_engine, text
import os

# Get DB URL from env or use default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/emergency_db")

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT id, username, role, can_take_duty, is_active FROM users WHERE username = 'marcel.wierich'"))
        user = result.fetchone()
        
        print("\n--- USER DEBUG INFO ---")
        if user:
            print(f"ID: {user[0]}")
            print(f"Username: '{user[1]}'")
            print(f"Role: '{user[2]}'")
            print(f"Can Take Duty: {user[3]}")
            print(f"Is Active: {user[4]}")
        else:
            print("User 'marcel.wierich' NOT FOUND in database.")
            
        print("-----------------------\n")
        
        # Check counts
        result_all = connection.execute(text("SELECT count(*) FROM users"))
        print(f"Total users: {result_all.scalar()}")

except Exception as e:
    print(f"Error connecting to DB: {e}")
