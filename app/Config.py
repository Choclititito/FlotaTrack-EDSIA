from pydantic_settings import BaseSettings, SettingsConfigDict
 
 
class Settings(BaseSettings):
    """Configuración de la app, siempre por variables de entorno.
 
    En esta versión temprana la base de datos por defecto es SQLite (un solo
    archivo, sin servidor que instalar) para poder correr todo con un simple
    entorno virtual. Más adelante, cuando se agregue Docker, esto cambia a
    PostgreSQL sin tocar el resto del código — por eso vive en settings y no
    hardcodeado en ningún otro archivo.
    """
 
    database_url: str = "sqlite:///./fleettrack.db"
    environment: str = "development"
 
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
 
 
settings = Settings()
 