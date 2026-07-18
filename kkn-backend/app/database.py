from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv  # Tambahkan ini

load_dotenv()  # Tambahkan ini untuk membuka "brankas" .env

# Mengambil URL dari .env
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency untuk mendapatkan session DB di setiap request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()