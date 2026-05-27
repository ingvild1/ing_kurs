from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Ping
from ..schemas import PingOut

router = APIRouter()


@router.post("/pings", response_model=PingOut, status_code=status.HTTP_201_CREATED)
def create_ping(db: Session = Depends(get_db)):
    ping = Ping()
    db.add(ping)
    db.commit()
    db.refresh(ping)
    return ping


@router.get("/pings", response_model=list[PingOut])
def list_pings(db: Session = Depends(get_db)):
    return db.query(Ping).order_by(Ping.created_at.desc()).all()
