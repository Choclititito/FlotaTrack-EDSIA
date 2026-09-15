import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TelemetryIn(BaseModel):
    latitude: float
    longitude: float
    speed_kmh: float = Field(ge=0)
    fuel_level_pct: float = Field(ge=0, le=100)
    acknowledged_command_id: str | None = None


class PendingCommandOut(BaseModel):
    type: str
    command_id: str


class TelemetryAck(BaseModel):
    received: bool
    pending_command: PendingCommandOut | None = None


class TruckCreate(BaseModel):
    plates: str
    model: str
    capacity_kg: float | None = None


class TruckOut(BaseModel):
    id: str
    plates: str
    model: str
    capacity_kg: float | None = None
    security_state: str

    model_config = ConfigDict(from_attributes=True)


class TruckStatusOut(BaseModel):
    truck: TruckOut
    latest_reading: dict | None = None


class KillSwitchRequest(BaseModel):
    action: str  # "lock" | "unlock"
    confirm: bool = False


class CommandOut(BaseModel):
    id: str
    truck_id: str
    type: str
    status: str
    requested_at: datetime.datetime
    applied_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class DriverCreate(BaseModel):
    name: str
    license_number: str | None = None
    phone: str | None = None


class DriverOut(BaseModel):
    id: str
    license_number: str | None = None
    name: str
    phone: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TripCreate(BaseModel):
    truck_id: str
    driver_id: str
    origin: str
    destination: str
    cargo_description: str | None = None


class TripOut(BaseModel):
    id: str
    truck_id: str
    driver_id: str
    origin: str
    destination: str
    cargo_description: str | None = None
    started_at: datetime.datetime
    finished_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CartaPorteCreate(BaseModel):
    folio: str

    # --- Datos fiscales generales ---
    emisor_rfc: str
    receptor_rfc: str
    tipo_cfdi: Literal["Ingreso", "Traslado"] = "Traslado"

    # --- Ubicación de origen ---
    origen_clave: str
    origen_calle: str
    origen_numero_exterior: str | None = None
    origen_numero_interior: str | None = None
    origen_colonia: str
    origen_localidad: str | None = None
    origen_municipio: str
    origen_estado: str
    origen_pais: str = "México"
    origen_codigo_postal: str
    origen_fecha_hora_salida: datetime.datetime

    # --- Ubicación de destino ---
    destino_clave: str
    destino_calle: str
    destino_numero_exterior: str | None = None
    destino_numero_interior: str | None = None
    destino_colonia: str
    destino_localidad: str | None = None
    destino_municipio: str
    destino_estado: str
    destino_pais: str = "México"
    destino_codigo_postal: str
    destino_fecha_hora_llegada: datetime.datetime

    distancia_recorrida_km: float = Field(ge=0)

    # --- Mercancía ---
    mercancia_clave_prod_serv: str
    merchandise_description: str
    mercancia_peso_bruto_kg: float = Field(ge=0)
    mercancia_peso_neto_kg: float = Field(ge=0)
    mercancia_clave_unidad: str
    material_peligroso: bool = False
    mercancia_embalaje: str | None = None

    # --- Datos del medio de transporte ---
    tipo_transporte: Literal["Terrestre", "Aéreo", "Marítimo", "Ferroviario"] = "Terrestre"
    config_vehicular: str
    placa_camion: str
    placa_remolque: str | None = None
    numero_permiso_sict: str
    aseguradora_nombre: str
    poliza_numero: str

    # --- Datos de la figura de transporte (operador) ---
    operador_nombre: str
    operador_rfc: str
    operador_licencia: str
    operador_domicilio: str


class CartaPorteOut(CartaPorteCreate):
    id: str
    trip_id: str

    model_config = ConfigDict(from_attributes=True)