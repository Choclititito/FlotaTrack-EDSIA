from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la app, siempre por variables de entorno (nunca hardcodeada)."""
 
    database_url: str = "postgresql://fleettrack:fleettrack@localhost:5432/fleettrack"
    environment: str = "development"
 
    # Credenciales compartidas para el front de captura de carta porte (empleados).
    # SIEMPRE sobreescribir esto por variables de entorno reales en producción.
    employee_username: str = "empleado"
    employee_password: str = "cambia-esta-clave"

    # Umbral de "detenido" para el kill switch (ver ADR-0002): el backend solo
    # marca un comando como aplicado si la lectura reporta velocidad <= a esto.
    # No es 0 exacto para tolerar ruido normal del sensor/GPS.
    kill_switch_speed_threshold_kmh: float = 2.0
 
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
 
 
settings = Settings()
 