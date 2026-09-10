from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/devices", tags=["telemetry"])

# Margen de tolerancia para considerar "detenido" (ruido normal de GPS/sensor).
# Nunca se aplica un cambio de security_state por encima de este umbral,
# sin importar lo que el dispositivo diga que ya hizo.
KILL_SWITCH_SAFE_SPEED_KMH = 0.5


@router.post("/{truck_id}/telemetry", response_model=schemas.TelemetryAck)
def ingest_telemetry(
    truck_id: str, payload: schemas.TelemetryIn, db: Session = Depends(get_db)
) -> schemas.TelemetryAck:
    """Recibe una lectura del dispositivo y, si aplica, gestiona el kill switch.

    Protocolo del kill switch (servidor -> dispositivo, nunca al revés):
    1. El despachador pide bloquear/desbloquear -> se crea un Command "pending".
    2. En su siguiente lectura normal, el dispositivo recibe ese comando aquí.
    3. El firmware decide si es seguro aplicarlo (solo si su velocidad
       reportada es 0) y, cuando lo aplica, lo confirma mandando
       `acknowledged_command_id` en su siguiente POST.
    4. El servidor NUNCA confía ciegamente en esa confirmación: solo la honra
       si `speed_kmh` en ese mismo request es prácticamente 0
       (KILL_SWITCH_SAFE_SPEED_KMH). Si no, el comando se queda "pending"
       aunque el dispositivo haya mandado el acknowledged_command_id.
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

    if payload.acknowledged_command_id:
        command = db.get(models.Command, payload.acknowledged_command_id)
        is_valid_target = (
            command is not None
            and command.truck_id == truck_id
            and command.status == models.CommandStatus.pending.value
        )
        if is_valid_target and payload.speed_kmh <= KILL_SWITCH_SAFE_SPEED_KMH:
            command.status = models.CommandStatus.applied.value
            command.applied_at = datetime.utcnow()
            truck.security_state = (
                models.SecurityState.locked.value
                if command.type == models.CommandType.lock.value
                else models.SecurityState.active.value
            )
        # Si la velocidad reportada no es prácticamente 0, la confirmación se
        # ignora por completo: el comando se queda "pending" y se le vuelve a
        # informar al dispositivo en la respuesta de abajo. No se confía en
        # que el dispositivo ya haya verificado esto por su cuenta.

    pending = (
        db.query(models.Command)
        .filter(
            models.Command.truck_id == truck_id,
            models.Command.status == models.CommandStatus.pending.value,
        )
        .order_by(models.Command.requested_at.asc())
        .first()
    )

    db.commit()

    pending_out = None
    if pending is not None:
        pending_out = schemas.PendingCommandOut(type=pending.type, command_id=pending.id)

    return schemas.TelemetryAck(received=True, pending_command=pending_out)