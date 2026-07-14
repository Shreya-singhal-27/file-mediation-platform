from sqlalchemy import text

from app.database.database import engine

try:
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version();"))
        print(version.scalar())

    print("Database Connected Successfully")

except Exception as e:
    print(e)