from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/devices", tags=["telemetry"])


@router.post("/{truck_id}/telemetry", response_model=schemas.TelemetryAck)
def ingest_telemetry(
    truck_id: str, payload: schemas.TelemetryIn, db: Session = Depends(get_db)
) -> schemas.TelemetryAck:
    """Recibe una lectura de telemetría y resuelve el protocolo de kill switch.

    Ver ADR-0002: el servidor nunca fuerza el corte. Aquí solo (a) le informa
    al dispositivo si hay un comando `pending`, y (b) si el dispositivo
    confirma haberlo aplicado (`acknowledged_command_id`), el backend
    revalida de forma independiente que la velocidad reportada esté por
    debajo del umbral de seguridad antes de darlo por `applied`. Si el
    dispositivo confirma yendo a mayor velocidad, la confirmación se ignora
    por completo y el comando sigue `pending`.
    """
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

    is_stopped = payload.speed_kmh <= settings.kill_switch_speed_threshold_kmh

    if payload.acknowledged_command_id is not None and is_stopped:
        command = (
            db.query(models.Command)
            .filter(
                models.Command.id == payload.acknowledged_command_id,
                models.Command.truck_id == truck_id,
                models.Command.status == models.CommandStatus.pending.value,
            )
            .first()
        )
        if command is not None:
            setattr(command, "status", models.CommandStatus.applied.value)
            setattr(command, "applied_at", datetime.utcnow())
            new_state = (
                models.SecurityState.locked.value
                if command.type == models.CommandType.lock.value
                else models.SecurityState.active.value
            )
            setattr(truck, "security_state", new_state)
    # Si acknowledged_command_id viene pero is_stopped es False, se ignora la
    # confirmación a propósito (no se toca el Command ni el truck): el
    # comando sigue pending y se le vuelve a informar abajo.

    db.commit()

    pending = (
        db.query(models.Command)
        .filter(
            models.Command.truck_id == truck_id,
            models.Command.status == models.CommandStatus.pending.value,
        )
        .order_by(models.Command.requested_at.desc())
        .first()
    )

    pending_out = None
    if pending is not None:
        pending_out = schemas.PendingCommandOut(
            type=str(pending.type), command_id=str(pending.id)
        )

    return schemas.TelemetryAck(received=True, pending_command=pending_out)
