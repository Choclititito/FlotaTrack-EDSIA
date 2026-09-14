from fastapi import APIRouter, Depends
 
from app.security import require_employee_auth
 
router = APIRouter(prefix="/auth", tags=["auth"])
 
 
@router.get("/check")
def check_credentials(username: str = Depends(require_employee_auth)) -> dict[str, str]:
    """El front de empleados llama esto al iniciar sesión para validar user/pass
    antes de mostrar el formulario — no hace nada más que confirmar que son
    correctos (401 si no)."""
    return {"status": "ok", "username": username}