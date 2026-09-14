from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app.routers import auth, drivers, telemetry, trips, trucks

app = FastAPI(title="FleetTrack API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://flotatrack-edsia.onrender.com",  # tu propio dominio en Render
        "http://localhost:8000",                   # para cuando pruebas local
        "null",                                     # para cuando abres el .html con doble clic (file://)
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

if settings.environment == "development":
    # Atajo solo para desarrollo local sin correr migraciones a mano.
    # En producción el esquema se crea/actualiza con "alembic upgrade head".
    Base.metadata.create_all(bind=engine)

app.include_router(trucks.router)
app.include_router(telemetry.router)
app.include_router(drivers.router)
app.include_router(trips.router)
app.include_router(auth.router)
# ...
app.mount("/panel", StaticFiles(directory="static", html=True), name="panel")
app.mount("/empleados", StaticFiles(directory="static-empleados", html=True), name="empleados")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}