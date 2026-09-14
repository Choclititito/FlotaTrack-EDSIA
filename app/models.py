import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class SecurityState(str, enum.Enum):
    active = "active"
    locked = "locked"


class CommandType(str, enum.Enum):
    lock = "lock"
    unlock = "unlock"


class CommandStatus(str, enum.Enum):
    pending = "pending"
    applied = "applied"
    cancelled = "cancelled"


class TipoCfdi(str, enum.Enum):
    ingreso = "Ingreso"
    traslado = "Traslado"


class TipoTransporte(str, enum.Enum):
    terrestre = "Terrestre"
    aereo = "Aéreo"
    maritimo = "Marítimo"
    ferroviario = "Ferroviario"


class Truck(Base):
    __tablename__ = "trucks"

    id = Column(String, primary_key=True, default=gen_uuid)
    plates = Column(String, unique=True, nullable=False)
    model = Column(String, nullable=False)
    capacity_kg = Column(Float, nullable=True)
    security_state = Column(String, default=SecurityState.active.value, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    telemetry_readings = relationship(
        "TelemetryReading", back_populates="truck", cascade="all, delete-orphan"
    )
    commands = relationship("Command", back_populates="truck", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="truck")


class TelemetryReading(Base):
    __tablename__ = "telemetry_readings"

    id = Column(String, primary_key=True, default=gen_uuid)
    truck_id = Column(String, ForeignKey("trucks.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed_kmh = Column(Float, nullable=False)
    fuel_level_pct = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    truck = relationship("Truck", back_populates="telemetry_readings")


class Command(Base):
    """Un comando pendiente de aplicar en el dispositivo (p. ej. el kill switch).

    El dispositivo es quien decide CUÁNDO aplicarlo (solo si está detenido) —
    el servidor únicamente informa que hay un comando en espera.
    """

    __tablename__ = "commands"

    id = Column(String, primary_key=True, default=gen_uuid)
    truck_id = Column(String, ForeignKey("trucks.id"), nullable=False)
    type = Column(String, nullable=False)  # "lock" | "unlock"
    status = Column(String, default=CommandStatus.pending.value, nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)

    truck = relationship("Truck", back_populates="commands")


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    license_number = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    trips = relationship("Trip", back_populates="driver")


class Trip(Base):
    __tablename__ = "trips"

    id = Column(String, primary_key=True, default=gen_uuid)
    truck_id = Column(String, ForeignKey("trucks.id"), nullable=False)
    driver_id = Column(String, ForeignKey("drivers.id"), nullable=False)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    cargo_description = Column(String, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    truck = relationship("Truck", back_populates="trips")
    driver = relationship("Driver", back_populates="trips")
    carta_porte = relationship(
        "CartaPorteRecord", back_populates="trip", uselist=False, cascade="all, delete-orphan"
    )


class CartaPorteRecord(Base):
    """Registro interno con los datos de un carta porte — no es el CFDI timbrado ante el SAT.

    Un solo registro por viaje: una mercancía, un tramo (origen-destino) y un
    remolque. Si más adelante se necesita soportar varias mercancías/tramos/
    remolques por viaje, esto tendría que pasar a tablas relacionadas.
    """

    __tablename__ = "carta_porte_records"

    id = Column(String, primary_key=True, default=gen_uuid)
    trip_id = Column(String, ForeignKey("trips.id"), unique=True, nullable=False)
    folio = Column(String, nullable=False)

    # --- Datos fiscales generales ---
    emisor_rfc = Column(String, nullable=False)
    receptor_rfc = Column(String, nullable=False)
    tipo_cfdi = Column(String, default=TipoCfdi.traslado.value, nullable=False)

    # --- Ubicación de origen ---
    origen_clave = Column(String, nullable=False)  # p. ej. "OR000001"
    origen_calle = Column(String, nullable=False)
    origen_numero_exterior = Column(String, nullable=True)
    origen_numero_interior = Column(String, nullable=True)
    origen_colonia = Column(String, nullable=False)
    origen_localidad = Column(String, nullable=True)
    origen_municipio = Column(String, nullable=False)
    origen_estado = Column(String, nullable=False)
    origen_pais = Column(String, default="México", nullable=False)
    origen_codigo_postal = Column(String, nullable=False)
    origen_fecha_hora_salida = Column(DateTime, nullable=False)

    # --- Ubicación de destino ---
    destino_clave = Column(String, nullable=False)  # p. ej. "DE000001"
    destino_calle = Column(String, nullable=False)
    destino_numero_exterior = Column(String, nullable=True)
    destino_numero_interior = Column(String, nullable=True)
    destino_colonia = Column(String, nullable=False)
    destino_localidad = Column(String, nullable=True)
    destino_municipio = Column(String, nullable=False)
    destino_estado = Column(String, nullable=False)
    destino_pais = Column(String, default="México", nullable=False)
    destino_codigo_postal = Column(String, nullable=False)
    destino_fecha_hora_llegada = Column(DateTime, nullable=False)

    distancia_recorrida_km = Column(Float, nullable=False)

    # --- Mercancía ---
    mercancia_clave_prod_serv = Column(String, nullable=False)
    merchandise_description = Column(String, nullable=False)
    mercancia_peso_bruto_kg = Column(Float, nullable=False)
    mercancia_peso_neto_kg = Column(Float, nullable=False)
    mercancia_clave_unidad = Column(String, nullable=False)
    material_peligroso = Column(Boolean, default=False, nullable=False)
    mercancia_embalaje = Column(String, nullable=True)  # solo si material_peligroso=True

    # --- Datos del medio de transporte ---
    tipo_transporte = Column(String, default=TipoTransporte.terrestre.value, nullable=False)
    config_vehicular = Column(String, nullable=False)
    placa_camion = Column(String, nullable=False)
    placa_remolque = Column(String, nullable=True)
    numero_permiso_sict = Column(String, nullable=False)
    aseguradora_nombre = Column(String, nullable=False)
    poliza_numero = Column(String, nullable=False)

    # --- Datos de la figura de transporte (operador) ---
    operador_nombre = Column(String, nullable=False)
    operador_rfc = Column(String, nullable=False)
    operador_licencia = Column(String, nullable=False)
    operador_domicilio = Column(String, nullable=False)

    trip = relationship("Trip", back_populates="carta_porte")