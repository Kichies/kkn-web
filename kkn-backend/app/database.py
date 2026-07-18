from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

load_dotenv()  # aman dipanggil walau di Vercel (env var sudah di-inject duluan)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL tidak ditemukan. "
        "Pastikan sudah diisi di file .env (lokal) atau di Environment Variables Vercel (production)."
    )

# NullPool penting untuk serverless: tiap request = koneksi baru dibuka lalu ditutup.
# Kalau pakai pool biasa, koneksi ke Supabase bisa cepat habis karena tiap
# cold start Vercel bikin instance baru yang tidak saling berbagi pool.
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    pool_pre_ping=True,
    connect_args={"sslmode": "require"},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()