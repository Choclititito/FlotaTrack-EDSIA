from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app.routers import drivers, telemetry, trips, trucks

# ...

app = FastAPI(title="FleetTrack API", version="0.1.0")

if settings.environment == "development":
    # Atajo solo para desarrollo local sin correr migraciones a mano.
    # En producción el esquema se crea/actualiza con "alembic upgrade head".
    Base.metadata.create_all(bind=engine)

app.include_router(trucks.router)
app.include_router(telemetry.router)
app.include_router(drivers.router)
app.include_router(trips.router)
# ...

app.mount("/panel", StaticFiles(directory="static", html=True), name="panel")

@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
