"""
Server pusat (central hub) Sistem Terdistribusi Pemantauan Ketersediaan
Lahan & Riwayat Parkir Kampus.

Setiap lahan parkir dipantau oleh sebuah "node/agent" independen
(lihat folder nodes/) yang secara berkala melaporkan jumlah slot
terisi ke endpoint POST /api/report. Server pusat menyimpan status
terkini + riwayat time-series, dan menyiarkan (broadcast) perubahan
secara real-time ke semua klien web via WebSocket.
"""
import json
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc
import os

from .database import Base, engine, get_db, SessionLocal
from .models import ParkingLot, ParkingHistory

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistem Pemantauan Parkir Kampus")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")


# ---------- Skema data (Pydantic) ----------
class ReportIn(BaseModel):
    lot_id: str
    name: Optional[str] = None
    location: Optional[str] = None
    total_slots: int = Field(gt=0)
    occupied_slots: int = Field(ge=0)
    node_id: Optional[str] = "unknown-node"


class LotOut(BaseModel):
    id: str
    name: str
    location: Optional[str]
    total_slots: int
    occupied_slots: int
    available_slots: int
    occupancy_rate: float
    status: str
    node_id: Optional[str]
    last_update: datetime

    class Config:
        from_attributes = True


class HistoryOut(BaseModel):
    occupied_slots: int
    total_slots: int
    timestamp: datetime
    node_id: Optional[str]

    class Config:
        from_attributes = True


# ---------- WebSocket broadcast manager ----------
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(message, default=str))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# ---------- Endpoint: node melaporkan status (write path) ----------
@app.post("/api/report")
async def report_status(payload: ReportIn, db: Session = Depends(get_db)):
    """Dipanggil oleh setiap node/agent lahan parkir untuk melaporkan okupansi terbaru."""
    lot = db.get(ParkingLot, payload.lot_id)
    now = datetime.utcnow()

    if lot is None:
        lot = ParkingLot(
            id=payload.lot_id,
            name=payload.name or payload.lot_id,
            location=payload.location,
            total_slots=payload.total_slots,
            occupied_slots=payload.occupied_slots,
            node_id=payload.node_id,
            last_update=now,
            status="online",
        )
        db.add(lot)
    else:
        lot.total_slots = payload.total_slots
        lot.occupied_slots = payload.occupied_slots
        lot.node_id = payload.node_id
        lot.last_update = now
        lot.status = "online"
        if payload.name:
            lot.name = payload.name
        if payload.location:
            lot.location = payload.location

    history_row = ParkingHistory(
        lot_id=payload.lot_id,
        occupied_slots=payload.occupied_slots,
        total_slots=payload.total_slots,
        timestamp=now,
        node_id=payload.node_id,
    )
    db.add(history_row)
    db.commit()
    db.refresh(lot)

    await manager.broadcast({
        "type": "update",
        "lot": LotOut.model_validate(lot).model_dump(),
    })

    return {"ok": True}


# ---------- Endpoint: baca status semua lahan (read path) ----------
@app.get("/api/lots", response_model=List[LotOut])
def list_lots(db: Session = Depends(get_db)):
    lots = db.query(ParkingLot).order_by(ParkingLot.id).all()
    return lots


@app.get("/api/lots/{lot_id}", response_model=LotOut)
def get_lot(lot_id: str, db: Session = Depends(get_db)):
    lot = db.get(ParkingLot, lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lahan parkir tidak ditemukan")
    return lot


@app.get("/api/lots/{lot_id}/history", response_model=List[HistoryOut])
def get_history(lot_id: str, limit: int = 100, db: Session = Depends(get_db)):
    rows = (
        db.query(ParkingHistory)
        .filter(ParkingHistory.lot_id == lot_id)
        .order_by(desc(ParkingHistory.timestamp))
        .limit(limit)
        .all()
    )
    return list(reversed(rows))


@app.get("/api/summary")
def summary(db: Session = Depends(get_db)):
    lots = db.query(ParkingLot).all()
    total = sum(l.total_slots for l in lots)
    occupied = sum(l.occupied_slots for l in lots)
    return {
        "total_lots": len(lots),
        "total_slots": total,
        "occupied_slots": occupied,
        "available_slots": total - occupied,
        "occupancy_rate": round((occupied / total) * 100, 1) if total else 0,
        "online_nodes": len([l for l in lots if l.status == "online"]),
    }


# ---------- WebSocket real-time ----------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive ping dari klien
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ---------- Serve web dashboard ----------
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))
