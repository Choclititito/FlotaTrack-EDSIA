from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.post("", response_model=schemas.DriverOut, status_code=201)
def create_driver(payload: schemas.DriverCreate, db: Session = Depends(get_db)) -> models.Driver:
    driver = models.Driver(
        name=payload.name, license_number=payload.license_number, phone=payload.phone
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver


@router.get("", response_model=list[schemas.DriverOut])
def list_drivers(db: Session = Depends(get_db)) -> list[models.Driver]:
    return db.query(models.Driver).all()


@router.get("/{driver_id}", response_model=schemas.DriverOut)
def get_driver(driver_id: str, db: Session = Depends(get_db)) -> models.Driver:
    driver = db.get(models.Driver, driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.get("/{driver_id}/trips", response_model=list[schemas.TripOut])
def list_driver_trips(driver_id: str, db: Session = Depends(get_db)) -> list[models.Trip]:
    """Historial de viajes del conductor: de dónde a dónde, y en qué camión."""
    driver = db.get(models.Driver, driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")

    return (
        db.query(models.Trip)
        .filter(models.Trip.driver_id == driver_id)
        .order_by(models.Trip.started_at.desc())
        .all()
    )
