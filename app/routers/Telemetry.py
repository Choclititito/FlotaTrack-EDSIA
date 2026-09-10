from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/devices", tags=["telemetry"])


@router.post("/{truck_id}/telemetry", response_model=schemas.TelemetryAck)
def ingest_telemetry(
    truck_id: str, payload: schemas.TelemetryIn, db: Session = Depends(get_db)
) -> schemas.TelemetryAck:
    truck = db.get(models.Truck, truck_id)
    if truck is None:
        raise HTTPException(status_code=404, detail="Truck not found")

    reading = models.TelemetryReading(
        truck_id=truck_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        speed_kmh=payload.speed_kmh,
        fuel_level_pct=payload.fuel_level_pct,
    )
    db.add(reading)
    db.commit()

    return schemas.TelemetryAck(received=True)