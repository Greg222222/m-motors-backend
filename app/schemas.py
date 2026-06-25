from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models import DossierStatus, DossierType, FuelType, Role, VehicleMode


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: Role
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VehicleCreate(BaseModel):
    brand: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1990, le=2100)
    mileage: int = Field(ge=0)
    color: str = Field(min_length=1, max_length=50)
    fuel_type: FuelType
    description: str = Field(default="", max_length=2000)
    image_url: str | None = Field(default=None, max_length=500)
    price_sale: float | None = Field(default=None, ge=0)
    price_rent_monthly: float | None = Field(default=None, ge=0)
    mode: VehicleMode


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brand: str
    model: str
    year: int
    mileage: int
    color: str
    fuel_type: FuelType
    description: str
    image_url: str | None
    price_sale: float | None
    price_rent_monthly: float | None
    mode: VehicleMode
    is_engaged: bool


class VehicleBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brand: str
    model: str
    year: int
    image_url: str | None


class VehicleModeUpdate(BaseModel):
    mode: VehicleMode


class DossierCreate(BaseModel):
    vehicle_id: int
    type: DossierType


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr


class DossierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    vehicle_id: int
    type: DossierType
    status: DossierStatus
    refusal_reason: str | None
    created_at: datetime
    vehicle: VehicleBrief
    user: UserBrief


class DossierDecision(BaseModel):
    approve: bool
    refusal_reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def check_refusal_reason(self) -> "DossierDecision":
        if not self.approve and not self.refusal_reason:
            raise ValueError("refusal_reason is required when approve is False")
        return self


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dossier_id: int
    filename: str
    content_type: str
    created_at: datetime
