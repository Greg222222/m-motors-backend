from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin
from app.models import Vehicle, VehicleMode
from app.schemas import VehicleCreate, VehicleModeUpdate, VehicleOut

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleOut])
def list_vehicles(mode: VehicleMode | None = None, db: Session = Depends(get_db)):
    """US-01: search the catalogue, optionally filtered by Achat/Location."""
    query = db.query(Vehicle)
    if mode is not None:
        query = query.filter((Vehicle.mode == mode) | (Vehicle.mode == VehicleMode.both))
    return query.order_by(Vehicle.id).all()


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """US-01: vehicle detail page (photo, description, full characteristics)."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle


@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VehicleCreate, db: Session = Depends(get_db), _admin=Depends(require_admin)
):
    """US-04: back-office adds a vehicle for sale, rent, or both."""
    if payload.mode in (VehicleMode.sale, VehicleMode.both) and payload.price_sale is None:
        raise HTTPException(status_code=422, detail="price_sale is required for this mode")
    if payload.mode in (VehicleMode.rent, VehicleMode.both) and payload.price_rent_monthly is None:
        raise HTTPException(status_code=422, detail="price_rent_monthly is required for this mode")

    vehicle = Vehicle(**payload.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.patch("/{vehicle_id}/mode", response_model=VehicleOut)
def update_vehicle_mode(
    vehicle_id: int,
    payload: VehicleModeUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """US-05: toggle a vehicle between Sale and Rent (or both)."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    if vehicle.is_engaged:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle is engaged in an ongoing dossier and cannot be switched",
        )
    vehicle.mode = payload.mode
    db.commit()
    db.refresh(vehicle)
    return vehicle
