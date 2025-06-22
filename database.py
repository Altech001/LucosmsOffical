from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:altech@001@localhost:5432/luco"

DB_URI = "postgresql://lucosms_fr6s_user:XW8sLMPg8BPAKJmKbyymPokMLJZx2oia@dpg-d1c5d8euk2gs73acoa8g-a.oregon-postgres.render.com/lucosms_fr6s"
# DB_URI = "postgresql://postgres:xecmKsNUQBtnuitVSwuKuzaVkGlnFmcT@shinkansen.proxy.rlwy.net:46354/railway"
engine = create_engine(DB_URI, connect_args={"sslmode": "require"})


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
