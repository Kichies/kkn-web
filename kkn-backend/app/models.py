from sqlalchemy import Column, Integer, String, Text, Date
from app.database import Base
from datetime import date

# --- TABEL BARU: KHUSUS ABSENSI PAGI ---
class Absensi(Base):
    __tablename__ = "absensi"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    tanggal = Column(Date, default=date.today)
    waktu = Column(String) 
    status_kehadiran = Column(String)

# --- TABEL LAMA: KHUSUS LOGBOOK MALAM ---
class Logbook(Base):
    __tablename__ = "logbooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    tanggal = Column(Date, default=date.today)
    kegiatan = Column(Text)
    foto = Column(Text, nullable=True)

class Cashflow(Base):
    __tablename__ = "cashflows"

    id = Column(Integer, primary_key=True, index=True)
    tipe = Column(String, index=True)
    nominal = Column(Integer)
    pic = Column(String)
    keterangan = Column(Text)
    tanggal = Column(Date, default=date.today)
    struk = Column(Text, nullable=True) 
    
class Proker(Base):
    __tablename__ = "prokers"

    id = Column(Integer, primary_key=True, index=True)
    judul = Column(String, index=True)
    deskripsi = Column(Text)
    pic = Column(String)
    tenggat = Column(String)
    status = Column(String, default="To-Do") # To-Do, In-Progress, Done