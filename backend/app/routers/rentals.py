from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from app.core.database import get_db
from app.models.models import InstrumentRental, Instrument, Student
from app.schemas.schemas import InstrumentRentalOut, InstrumentRentalCreate, InstrumentRentalReturn
from app.routers.auth import get_current_user, require_role

router = APIRouter()

@router.get("", response_model=List[InstrumentRentalOut])
def list_rentals(
    status: Optional[str] = None,
    instrument_id: Optional[int] = None,
    student_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(InstrumentRental)
    if status: q = q.filter(InstrumentRental.status == status)
    if instrument_id: q = q.filter(InstrumentRental.instrument_id == instrument_id)
    if student_id: q = q.filter(InstrumentRental.student_id == student_id)
    return q.order_by(InstrumentRental.created_at.desc()).all()

@router.post("", response_model=InstrumentRentalOut)
def create_rental(
    data: InstrumentRentalCreate,
    db: Session = Depends(get_db),
    _=require_role("admin", "manager")
):
    instrument = db.query(Instrument).filter(Instrument.id == data.instrument_id).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="乐器不存在")
    if instrument.status != 'available':
        raise HTTPException(status_code=400, detail="该乐器当前不可租赁")
    q = db.query(InstrumentRental).filter(
        InstrumentRental.instrument_id == data.instrument_id,
        InstrumentRental.status == 'active'
    )
    if q.first():
        raise HTTPException(status_code=400, detail="该乐器已被出租")
    student = db.query(Student).filter(Student.id == data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")
    rental = InstrumentRental(**data.dict())
    db.add(rental)
    instrument.status = 'rented'
    db.commit()
    db.refresh(rental)
    return rental

@router.post("/{rid}/return", response_model=InstrumentRentalOut)
def return_rental(
    rid: int,
    data: InstrumentRentalReturn,
    db: Session = Depends(get_db),
    _=require_role("admin", "manager")
):
    rental = db.query(InstrumentRental).filter(InstrumentRental.id == rid).first()
    if not rental:
        raise HTTPException(status_code=404, detail="租赁记录不存在")
    if rental.status != 'active':
        raise HTTPException(status_code=400, detail="该租赁记录已归还")
    rental.actual_return_date = data.actual_return_date
    rental.return_check = data.return_check
    rental.damage_description = data.damage_description
    rental.status = 'returned'
    instrument = db.query(Instrument).filter(Instrument.id == rental.instrument_id).first()
    if instrument:
        instrument.status = 'available'
    db.commit()
    db.refresh(rental)
    return rental

@router.get("/{rid}", response_model=InstrumentRentalOut)
def get_rental(
    rid: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    rental = db.query(InstrumentRental).filter(InstrumentRental.id == rid).first()
    if not rental:
        raise HTTPException(status_code=404, detail="租赁记录不存在")
    return rental

@router.put("/{rid}/deposit")
def update_deposit_status(
    rid: int,
    deposit_status: str,
    db: Session = Depends(get_db),
    _=require_role("admin", "manager")
):
    rental = db.query(InstrumentRental).filter(InstrumentRental.id == rid).first()
    if not rental:
        raise HTTPException(status_code=404, detail="租赁记录不存在")
    rental.deposit_status = deposit_status
    db.commit()
    return {"message": "押金状态已更新"}

@router.get("/reminders/expiring", response_model=List[InstrumentRentalOut])
def expiring_reminders(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    end_date = date.today() + timedelta(days=days)
    q = db.query(InstrumentRental).filter(
        InstrumentRental.status == 'active',
        InstrumentRental.end_date <= end_date,
        InstrumentRental.end_date >= date.today()
    )
    return q.order_by(InstrumentRental.end_date).all()

@router.get("/reminders/overdue", response_model=List[InstrumentRentalOut])
def overdue_reminders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(InstrumentRental).filter(
        InstrumentRental.status == 'active',
        InstrumentRental.end_date < date.today()
    )
    return q.order_by(InstrumentRental.end_date).all()