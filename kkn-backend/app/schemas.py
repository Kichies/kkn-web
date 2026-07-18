from pydantic import BaseModel
from datetime import date
from typing import Optional

# --- SCHEMAS: ABSENSI ---
class AbsensiCreate(BaseModel):
    user_id: int
    status_kehadiran: str
    waktu: str
    tanggal: Optional[date] = None

class AbsensiResponse(AbsensiCreate):
    id: int
    class Config:
        from_attributes = True

# --- SCHEMAS: LOGBOOK ---
class LogbookCreate(BaseModel):
    user_id: int
    kegiatan: str
    tanggal: Optional[date] = None
    foto: Optional[str] = None 

class LogbookResponse(LogbookCreate):
    id: int
    class Config:
        from_attributes = True

# --- SCHEMAS: CASHFLOW ---
class CashflowCreate(BaseModel):
    tipe: str
    nominal: int
    pic: str
    keterangan: str
    tanggal: Optional[date] = None
    struk: Optional[str] = None 

class CashflowResponse(CashflowCreate):
    id: int
    class Config:
        from_attributes = True

class ProkerCreate(BaseModel):
    judul: str
    deskripsi: str
    pic: str
    tenggat: str
    status: str = "To-Do"

class ProkerStatusUpdate(BaseModel):
    status: str

class ProkerResponse(ProkerCreate):
    id: int
    class Config:
        from_attributes = True