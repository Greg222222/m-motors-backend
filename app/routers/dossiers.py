from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Dossier, User, Vehicle
from app.schemas import DossierCreate, DossierOut

router = APIRouter(prefix="/dossiers", tags=["dossiers"])


@router.post("", response_model=DossierOut, status_code=status.HTTP_201_CREATED)
def create_dossier(
    payload: DossierCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """US-02: a registered client opens an Achat/Location dossier for a vehicle."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    dossier = Dossier(user_id=user.id, vehicle_id=vehicle.id, type=payload.type)
    vehicle.is_engaged = True
    db.add(dossier)
    db.commit()
    db.refresh(dossier)
    return dossier


@router.get("/me", response_model=list[DossierOut])
def my_dossiers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """US-03: a client follows the real-time status of their own dossiers."""
    return db.query(Dossier).filter(Dossier.user_id == user.id).order_by(Dossier.id).all()
