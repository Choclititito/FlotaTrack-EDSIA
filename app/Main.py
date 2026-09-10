from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.routers import telemetry, trucks

app = FastAPI(title="FleetTrack API (versión temprana)", version="0.1.0")

if settings.environment == "development":
    # Atajo para desarrollo local sin migraciones todavía (esta versión
    # temprana no incluye Alembic/Docker — eso se agrega en una etapa
    # posterior del proyecto).
    Base.metadata.create_all(bind=engine)

app.include_router(trucks.router)
app.include_router(telemetry.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}