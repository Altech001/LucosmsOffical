from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:altech@001@localhost:5432/luco"

DB_URI = "postgresql://testdb_ejog_user:LDlnkCB0nhP1OwmputkywIEncu6p5mPX@dpg-d0oa11re5dus73b9g6a0-a.oregon-postgres.render.com/testdb_ejog"
# DB_URI = "postgresql://altech:DJ2ef3UJY1MnJYivE5fsPTNtjz9KYske@dpg-d0002ba4d50c739pjvqg-a.virginia-postgres.render.com/luco_sms"
engine = create_engine(DB_URI, connect_args={"sslmode": "require"})


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
