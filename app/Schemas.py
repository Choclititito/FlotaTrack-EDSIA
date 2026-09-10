from pydantic import BaseModel, ConfigDict, Field


class TelemetryIn(BaseModel):
    latitude: float
    longitude: float
    speed_kmh: float = Field(ge=0)
    fuel_level_pct: float = Field(ge=0, le=100)


class TelemetryAck(BaseModel):
    received: bool


class TruckCreate(BaseModel):
    plates: str
    model: str
    capacity_kg: float | None = None


class TruckOut(BaseModel):
    id: str
    plates: str
    model: str
    capacity_kg: float | None = None

    model_config = ConfigDict(from_attributes=True)


class TruckStatusOut(BaseModel):
    truck: TruckOut
    latest_reading: dict | None = None