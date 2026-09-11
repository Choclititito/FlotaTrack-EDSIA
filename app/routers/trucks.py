from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/trucks", tags=["trucks"])


@router.post("", response_model=schemas.TruckOut, status_code=201)
def create_truck(payload: schemas.TruckCreate, db: Session = Depends(get_db)) -> models.Truck:
    truck = models.Truck(
        plates=payload.plates, model=payload.model, capacity_kg=payload.capacity_kg
    )
    db.add(truck)
    db.commit()
    db.refresh(truck)
    return truck


@router.get("", response_model=list[schemas.TruckOut])
def list_trucks(db: Session = Depends(get_db)) -> list[models.Truck]:
    return db.query(models.Truck).all()


@router.get("/{truck_id}/status", response_model=schemas.TruckStatusOut)
def truck_status(truck_id: str, db: Session = Depends(get_db)) -> schemas.TruckStatusOut:
    truck = db.get(models.Truck, truck_id)
    if truck is None:
        raise HTTPException(status_code=404, detail="Truck not found")

    latest = (
        db.query(models.TelemetryReading)
        .filter(models.TelemetryReading.truck_id == truck_id)
        .order_by(models.TelemetryReading.recorded_at.desc())
        .first()
    )

    latest_out = None
    if latest is not None:
        latest_out = {
            "latitude": latest.latitude,
            "longitude": latest.longitude,
            "speed_kmh": latest.speed_kmh,
            "fuel_level_pct": latest.fuel_level_pct,
            "recorded_at": latest.recorded_at.isoformat() if latest.recorded_at else None,
        }

    return schemas.TruckStatusOut(truck=truck, latest_reading=latest_out)


@router.post("/{truck_id}/kill-switch", response_model=schemas.CommandOut, status_code=201)
def request_kill_switch(
    truck_id: str, payload: schemas.KillSwitchRequest, db: Session = Depends(get_db)
) -> models.Command:
    """Solicita bloquear/desbloquear el camión. Requiere confirmación explícita.

    Esto solo CREA el comando pendiente — el corte real lo aplica el propio
    dispositivo cuando detecta que el vehículo está detenido (ver telemetry.py).
    """
    if not payload.confirm:
        raise HTTPException(
            status_code=400, detail="Se requiere confirmación explícita (confirm=true)"
        )

    if payload.action not in (models.CommandType.lock.value, models.CommandType.unlock.value):
        raise HTTPException(status_code=400, detail="action debe ser 'lock' o 'unlock'")

    truck = db.get(models.Truck, truck_id)
    if truck is None:
        raise HTTPException(status_code=404, detail="Truck not found")

    # Cualquier comando pendiente anterior de este camión queda cancelado: la
    # orden más reciente siempre es la que manda, nunca deben competir dos
    # comandos pendientes por el mismo camión.
    db.query(models.Command).filter(
        models.Command.truck_id == truck_id,
        models.Command.status == models.CommandStatus.pending.value,
    ).update({"status": models.CommandStatus.cancelled.value})

    command = models.Command(truck_id=truck_id, type=payload.action)
    db.add(command)
    db.commit()
    db.refresh(command)
    return command

