import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, enum.Enum):
    client = "client"
    admin = "admin"


class VehicleMode(str, enum.Enum):
    sale = "sale"
    rent = "rent"
    both = "both"


class DossierType(str, enum.Enum):
    achat = "achat"
    location = "location"


class DossierStatus(str, enum.Enum):
    en_attente = "en_attente"
    valide = "valide"
    refuse = "refuse"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.client, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    dossiers: Mapped[list["Dossier"]] = relationship(back_populates="user")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    mileage: Mapped[int] = mapped_column(Integer, nullable=False)
    price_sale: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_rent_monthly: Mapped[float | None] = mapped_column(Float, nullable=True)
    mode: Mapped[VehicleMode] = mapped_column(Enum(VehicleMode), nullable=False)
    is_engaged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    dossiers: Mapped[list["Dossier"]] = relationship(back_populates="vehicle")


class Dossier(Base):
    __tablename__ = "dossiers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    type: Mapped[DossierType] = mapped_column(Enum(DossierType), nullable=False)
    status: Mapped[DossierStatus] = mapped_column(Enum(DossierStatus), default=DossierStatus.en_attente)
    refusal_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship(back_populates="dossiers")
    vehicle: Mapped["Vehicle"] = relationship(back_populates="dossiers")
    documents: Mapped[list["Document"]] = relationship(back_populates="dossier", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dossier_id: Mapped[int] = mapped_column(ForeignKey("dossiers.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    dossier: Mapped["Dossier"] = relationship(back_populates="documents")
