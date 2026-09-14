from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la app, siempre por variables de entorno (nunca hardcodeada)."""
 
    database_url: str = "postgresql://fleettrack:fleettrack@localhost:5432/fleettrack"
    environment: str = "development"
 
    # Credenciales compartidas para el front de captura de carta porte (empleados).
    # SIEMPRE sobreescribir esto por variables de entorno reales en producción.
    employee_username: str = "empleado"
    employee_password: str = "cambia-esta-clave"
 
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
 
 
settings = Settings()
 