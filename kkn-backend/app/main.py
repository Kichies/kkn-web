from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- TAMBAHAN IMPORT UNTUK FILE UPLOAD ---
from fastapi.staticfiles import StaticFiles
import os
import base64
import uuid

from app import models
from app import schemas
from app.database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Manajemen KKN")

# --- KONFIGURASI FOLDER UPLOADS & CORS ---
os.makedirs("app/uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500", "*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- FUNGSI SULAP BASE64 KE FILE GAMBAR ---
def process_base64_image(base64_str: str) -> str:
    """Ubah teks Base64 jadi gambar JPG/PNG dan kembalikan URL-nya"""
    if not base64_str or not base64_str.startswith("data:image"):
        return base64_str # Kembalikan teks asli jika kosong atau sudah berupa URL
    try:
        header, encoded = base64_str.split(",", 1)
        ext = header.split(";")[0].split("/")[1]
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join("app/uploads", filename)
        
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(encoded))
            
        return f"http://127.0.0.1:8000/uploads/{filename}"
    except Exception as e:
        print(f"Gagal memproses gambar: {e}")
        return None

# ==========================================
# KONFIGURASI GOOGLE SHEETS (Live Report)
# ==========================================
def append_to_sheet(data_absensi, nama_user):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("app/credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("Absensi KKN 2026").worksheet("Data Mentah")
        
        jam = int(data_absensi.waktu.split(":")[0])
        sesi = "Pagi" if jam < 15 else "Malam"
        baris_baru = [str(data_absensi.tanggal), data_absensi.waktu, sesi, nama_user, data_absensi.status_kehadiran]
        
        sheet.append_row(baris_baru)
        print("Berhasil mengirim data absensi ke Tab Data Mentah!")
    except Exception as e:
        print(f"Gagal mengirim ke Google Sheets: {e}")

@app.get("/")
def read_root():
    return {"message": "Selamat datang di API KKN Kades Keren!"}

# ==========================================
# ENDPOINT: ABSENSI (Scan QR Pagi & Malam)
# ==========================================
@app.post("/absensi/", response_model=schemas.AbsensiResponse, tags=["Absensi"])
def create_absensi(absensi: schemas.AbsensiCreate, db: Session = Depends(get_db)):
    # --- LOGIKA MESIN WAKTU (SATPAM JAM KERJA) ---
    jam = int(absensi.waktu.split(":")[0])
    
    if jam < 6:
        raise HTTPException(status_code=400, detail="Sabar Bos! Absen pagi baru dibuka jam 06:00.")
    elif 15 <= jam < 20:
        raise HTTPException(status_code=400, detail="Belum waktunya! Absen malam baru dibuka jam 20:00.")
    # ---------------------------------------------

    db_absensi = models.Absensi(
        user_id=absensi.user_id,
        status_kehadiran=absensi.status_kehadiran,
        waktu=absensi.waktu,
        tanggal=absensi.tanggal
    )
    db.add(db_absensi)
    db.commit()
    db.refresh(db_absensi)
    
    users_map = {
        1: "Hanif (Ketua)", 2: "Anin (Sekretaris)", 3: "Reva (Bendahara)", 
        4: "Davina (PDD)", 5: "Hardi (PDD)", 6: "Nhay (PDD)", 7: "Rivanza (Acara)", 
        8: "Amanda (Acara)", 9: "Alya (Acara)", 10: "Akmal (Humlog + Wakordes)", 
        11: "Rifqi (Humlog)", 12: "Vera (Humlog)", 13: "Azel (Konsumsi)", 14: "Apriyani (Konsumsi)"
    }
    nama = users_map.get(absensi.user_id, f"User {absensi.user_id}")
    append_to_sheet(absensi, nama)
    return db_absensi

@app.get("/absensi/", response_model=List[schemas.AbsensiResponse], tags=["Absensi"])
def read_absensi(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(models.Absensi).order_by(models.Absensi.id.desc()).offset(skip).limit(limit).all()

# ==========================================
# ENDPOINT: LOGBOOK (Laporan Malam Hari + Foto)
# ==========================================
@app.post("/logbook/", response_model=schemas.LogbookResponse, tags=["Logbook"])
def create_logbook(logbook: schemas.LogbookCreate, db: Session = Depends(get_db)):
    foto_url = process_base64_image(logbook.foto) # Panggil fungsi sihir
    db_logbook = models.Logbook(
        user_id=logbook.user_id,
        kegiatan=logbook.kegiatan,
        tanggal=logbook.tanggal,
        foto=foto_url 
    )
    db.add(db_logbook)
    db.commit()
    db.refresh(db_logbook)
    return db_logbook

@app.get("/logbook/", response_model=List[schemas.LogbookResponse], tags=["Logbook"])
def read_logbooks(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(models.Logbook).order_by(models.Logbook.id.desc()).offset(skip).limit(limit).all()

@app.delete("/logbook/{id}", tags=["Logbook"])
def delete_logbook(id: int, db: Session = Depends(get_db)):
    item = db.query(models.Logbook).filter(models.Logbook.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Data logbook tidak ditemukan")
    db.delete(item)
    db.commit()
    return {"message": f"Logbook ID {id} berhasil dihapus"}

@app.put("/logbook/{id}", response_model=schemas.LogbookResponse, tags=["Logbook"])
def update_logbook(id: int, logbook: schemas.LogbookCreate, db: Session = Depends(get_db)):
    item = db.query(models.Logbook).filter(models.Logbook.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Data logbook tidak ditemukan")
    
    item.user_id = logbook.user_id
    item.kegiatan = logbook.kegiatan
    item.tanggal = logbook.tanggal
    if logbook.foto:
        item.foto = process_base64_image(logbook.foto)
        
    db.commit()
    db.refresh(item)
    return item

# ==========================================
# ENDPOINT: CASHFLOW (Manajemen Keuangan)
# ==========================================
@app.post("/cashflow/", response_model=schemas.CashflowResponse, tags=["Cashflow"])
def create_cashflow(cashflow: schemas.CashflowCreate, db: Session = Depends(get_db)):
    struk_url = process_base64_image(cashflow.struk) # Panggil fungsi sihir
    db_cashflow = models.Cashflow(
        tipe=cashflow.tipe,
        nominal=cashflow.nominal,
        pic=cashflow.pic,
        keterangan=cashflow.keterangan,
        tanggal=cashflow.tanggal,
        struk=struk_url
    )
    db.add(db_cashflow)
    db.commit()
    db.refresh(db_cashflow)
    return db_cashflow

@app.get("/cashflow/", response_model=List[schemas.CashflowResponse], tags=["Cashflow"])
def read_cashflows(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(models.Cashflow).order_by(models.Cashflow.id.desc()).offset(skip).limit(limit).all()

@app.delete("/cashflow/{id}", tags=["Cashflow"])
def delete_cashflow(id: int, db: Session = Depends(get_db)):
    item = db.query(models.Cashflow).filter(models.Cashflow.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Data kas tidak ditemukan")
    db.delete(item)
    db.commit()
    return {"message": f"Transaksi ID {id} berhasil dihapus"}

@app.put("/cashflow/{id}", response_model=schemas.CashflowResponse, tags=["Cashflow"])
def update_cashflow(id: int, cashflow: schemas.CashflowCreate, db: Session = Depends(get_db)):
    item = db.query(models.Cashflow).filter(models.Cashflow.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Data kas tidak ditemukan")
    
    item.tipe = cashflow.tipe
    item.nominal = cashflow.nominal
    item.pic = cashflow.pic
    item.keterangan = cashflow.keterangan
    item.tanggal = cashflow.tanggal
    if cashflow.struk:
        item.struk = process_base64_image(cashflow.struk)
        
    db.commit()
    db.refresh(item)
    return item

# ==========================================
# ENDPOINT: PROGRAM KERJA (KANBAN BOARD)
# ==========================================
@app.post("/proker/", response_model=schemas.ProkerResponse, tags=["Proker"])
def create_proker(proker: schemas.ProkerCreate, db: Session = Depends(get_db)):
    db_proker = models.Proker(**proker.dict())
    db.add(db_proker)
    db.commit()
    db.refresh(db_proker)
    return db_proker

@app.get("/proker/", response_model=List[schemas.ProkerResponse], tags=["Proker"])
def read_prokers(db: Session = Depends(get_db)):
    return db.query(models.Proker).order_by(models.Proker.id.desc()).all()

@app.put("/proker/{id}", response_model=schemas.ProkerResponse, tags=["Proker"])
def update_proker(id: int, proker: schemas.ProkerCreate, db: Session = Depends(get_db)):
    item = db.query(models.Proker).filter(models.Proker.id == id).first()
    if not item: raise HTTPException(status_code=404)
    for key, value in proker.dict().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item

# Endpoint khusus kilat untuk Drag-and-Drop
@app.patch("/proker/{id}/status", tags=["Proker"])
def update_proker_status(id: int, status_update: schemas.ProkerStatusUpdate, db: Session = Depends(get_db)):
    item = db.query(models.Proker).filter(models.Proker.id == id).first()
    if not item: raise HTTPException(status_code=404)
    item.status = status_update.status
    db.commit()
    return {"message": "Status updated"}

@app.delete("/proker/{id}", tags=["Proker"])
def delete_proker(id: int, db: Session = Depends(get_db)):
    item = db.query(models.Proker).filter(models.Proker.id == id).first()
    if not item: raise HTTPException(status_code=404)
    db.delete(item)
    db.commit()
    return {"message": "Proker dihapus"}