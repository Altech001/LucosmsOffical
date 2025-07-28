from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DB_URI = "postgresql://lucosms_w46s_user:UD5A6LCCY9ujR7cN3lXcYY0fnIMrAogv@dpg-d23fadre5dus73aip1h0-a.oregon-postgres.render.com/lucosms_w46s"

engine = create_engine(DB_URI, connect_args={"sslmode": "require"})


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
