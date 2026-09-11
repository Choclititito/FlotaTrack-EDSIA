from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("", response_model=schemas.TripOut, status_code=201)
def create_trip(payload: schemas.TripCreate, db: Session = Depends(get_db)) -> models.Trip:
    truck = db.get(models.Truck, payload.truck_id)
    if truck is None:
        raise HTTPException(status_code=404, detail="Truck not found")

    driver = db.get(models.Driver, payload.driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")

    trip = models.Trip(
        truck_id=payload.truck_id,
        driver_id=payload.driver_id,
        origin=payload.origin,
        destination=payload.destination,
        cargo_description=payload.cargo_description,
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


@router.get("", response_model=list[schemas.TripOut])
def list_trips(db: Session = Depends(get_db)) -> list[models.Trip]:
    return db.query(models.Trip).order_by(models.Trip.started_at.desc()).all()


@router.get("/{trip_id}", response_model=schemas.TripOut)
def get_trip(trip_id: str, db: Session = Depends(get_db)) -> models.Trip:
    trip = db.get(models.Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.post("/{trip_id}/carta-porte", response_model=schemas.CartaPorteOut)
def upsert_carta_porte(
    trip_id: str,
    payload: schemas.CartaPorteCreate,
    response: Response,
    db: Session = Depends(get_db),
) -> models.CartaPorteRecord:
    """Crea o actualiza el registro de carta porte de un viaje.

    Es un registro interno del sistema (folio, mercancía, peso, config. de
    transporte) — NO es el CFDI de Carta Porte timbrado ante el SAT, eso queda
    fuera de alcance del reto. Un viaje solo tiene un registro de carta porte,
    así que si ya existía se actualiza (200) en vez de duplicarse (201).
    """
    trip = db.get(models.Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    record = (
        db.query(models.CartaPorteRecord)
        .filter(models.CartaPorteRecord.trip_id == trip_id)
        .first()
    )

    if record is None:
        record = models.CartaPorteRecord(trip_id=trip_id)
        db.add(record)
        response.status_code = 201
    else:
        response.status_code = 200

    # Cambio: Se añaden las directivas type: ignore para omitir el falso positivo
    record.folio = payload.folio  # type: ignore[assignment]
    record.merchandise_description = payload.merchandise_description  # type: ignore[assignment]
    record.weight_kg = payload.weight_kg  # type: ignore[assignment]
    record.transport_config = payload.transport_config  # type: ignore[assignment]

    db.commit()
    db.refresh(record)
    return record


@router.get("/{trip_id}/carta-porte", response_model=schemas.CartaPorteOut)
def get_carta_porte(trip_id: str, db: Session = Depends(get_db)) -> models.CartaPorteRecord:
    trip = db.get(models.Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    record = (
        db.query(models.CartaPorteRecord)
        .filter(models.CartaPorteRecord.trip_id == trip_id)
        .first()
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Carta porte not registered for this trip")
    return record

