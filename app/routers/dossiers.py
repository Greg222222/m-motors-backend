from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models import Dossier, DossierStatus, User, Vehicle
from app.schemas import DossierCreate, DossierDecision, DossierOut

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


@router.get("", response_model=list[DossierOut])
def list_all_dossiers(
    status_filter: DossierStatus | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """US-06: back-office lists every dossier, optionally filtered by status."""
    query = db.query(Dossier)
    if status_filter is not None:
        query = query.filter(Dossier.status == status_filter)
    return query.order_by(Dossier.id).all()


@router.post("/{dossier_id}/decision", response_model=DossierOut)
def decide_dossier(
    dossier_id: int,
    payload: DossierDecision,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """US-06: back-office validates or refuses a dossier (refusal requires a reason)."""
    dossier = db.query(Dossier).filter(Dossier.id == dossier_id).first()
    if dossier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dossier not found")
    if dossier.status != DossierStatus.en_attente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dossier already decided")

    if payload.approve:
        dossier.status = DossierStatus.valide
    else:
        dossier.status = DossierStatus.refuse
        dossier.refusal_reason = payload.refusal_reason
        vehicle = db.query(Vehicle).filter(Vehicle.id == dossier.vehicle_id).first()
        if vehicle is not None:
            vehicle.is_engaged = False

    db.commit()
    db.refresh(dossier)
    return dossier
