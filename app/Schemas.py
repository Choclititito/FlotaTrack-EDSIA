import datetime
from pydantic import BaseModel, ConfigDict, Field

class TelemetryIn(BaseModel):
    latitude: float
    longitude: float
    speed_kmh: float = Field(ge=0)
    fuel_level_pct: float = Field(ge=0, le=100)
    acknowledged_command_id: str | None = None

class PendingCommandOut(BaseModel):
    type: str
    command_id: str


class TelemetryAck(BaseModel):
    received: bool
    pending_command: PendingCommandOut | None = None


class TruckCreate(BaseModel):
    plates: str
    model: str
    capacity_kg: float | None = None

class TruckOut(BaseModel):
    id: str
    plates: str
    model: str
    capacity_kg: float | None = None
    security_state: str

    model_config = ConfigDict(from_attributes=True)


class TruckStatusOut(BaseModel):
    truck: TruckOut
    latest_reading: dict | None = None


class KillSwitchRequest(BaseModel):
    action: str  # "lock" | "unlock"
    confirm: bool = False


class CommandOut(BaseModel):
    id: str
    truck_id: str
    type: str
    status: str
    requested_at: datetime.datetime
    applied_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class DriverCreate(BaseModel):
    name: str
    license_number: str | None = None
    phone: str | None = None


class DriverOut(BaseModel):
    id: str
    name: str
    license_number: str | None = None
    phone: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TripCreate(BaseModel):
    truck_id: str
    driver_id: str
    origin: str
    destination: str
    cargo_description: str | None = None


class TripOut(BaseModel):
    id: str
    truck_id: str
    driver_id: str
    origin: str
    destination: str
    cargo_description: str | None = None
    started_at: datetime.datetime
    finished_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CartaPorteCreate(BaseModel):
    folio: str
    merchandise_description: str
    weight_kg: float | None = None
    transport_config: str | None = None


class CartaPorteOut(BaseModel):
    id: str
    trip_id: str
    folio: str
    merchandise_description: str
    weight_kg: float | None = None
    transport_config: str | None = None

    model_config = ConfigDict(from_attributes=True)