import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import settings

security = HTTPBasic()


def require_employee_auth(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Verifica el usuario/contraseña compartidos del front de empleados.

    Usa comparación en tiempo constante (secrets.compare_digest) para no dar
    pistas de timing sobre qué tan correcta es la credencial mandada.
    """
    valid_username = secrets.compare_digest(credentials.username, settings.employee_username)
    valid_password = secrets.compare_digest(credentials.password, settings.employee_password)

    if not (valid_username and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username