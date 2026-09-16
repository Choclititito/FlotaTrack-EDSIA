# Links de Render 
panel 
https://flotatrack-edsia.onrender.com/panel/

Empleados 
https://flotatrack-edsia.onrender.com/empleados/

Usuario: empleado

contraseña : test_1

Docs
https://flotatrack-edsia.onrender.com/docs

# FleetTrack — backend + paneles web

Backend del sistema de monitoreo de flotilla: telemetría, kill switch remoto antirrobo, registro de
carta porte por viaje (según el complemento del SAT) y dos paneles web (administración y captura de carta porte para
empleados).

## Stack

FastAPI + PostgreSQL + SQLAlchemy + Alembic, contenerizado con Docker. Los paneles web son HTML/JS plano (sin build
step), servidos como archivos estáticos desde el propio backend. El PDF de carta porte se genera con `reportlab`.

## Cómo correrlo localmente

```bash
cp .env.example .env
docker compose up --build
```

La API queda en http://localhost:8000, con `/health` y `/docs` (Swagger UI).

`docker-compose.yml` monta la carpeta local dentro del contenedor (`.:/app`), así que cualquier migración que genere
con Alembic aparece directo en el disco.

## Paneles web

| Panel | Ruta | Para quién | Autenticación |
|---|---|---|---|
| Administración | `/panel` | Despachadores / administración | Ninguna |
| Captura de carta porte | `/empleados` | Empleados que registran carta porte | Usuario/contraseña compartidos (`EMPLOYEE_USERNAME` / `EMPLOYEE_PASSWORD`) |

El panel de administración muestra camiones en vivo (mapa, telemetría, kill switch, historial), permite dar de alta
camiones/conductores/viajes, y trazar la ruta real entre origen y destino de un viaje (geocodificación con Nominatim +
ruteo con OSRM — servicios públicos gratuitos, sin garantía de disponibilidad; si fallan, se muestra una línea recta
como respaldo).

El panel de empleados captura los datos completos de carta porte de un viaje y permite editarlos si ya existían.

## Simular un dispositivo sin hardware real

1. Crea un camión:
   ```bash
   curl -X POST http://localhost:8000/trucks \
     -H "Content-Type: application/json" \
     -d '{"plates": "ABC-123", "model": "Kenworth T680", "capacity_kg": 20000}'
   ```
2. Copia el `id` que regresa y corre el simulador:
   ```bash
   pip install requests
   python scripts/simulate_device.py --truck-id <ID_DEL_CAMION>
   ```

## Kill switch (antirrobo)

```bash
curl -X POST http://localhost:8000/trucks/<ID_DEL_CAMION>/kill-switch \
  -H "Content-Type: application/json" \
  -d '{"action": "lock", "confirm": true}'
```

Por seguridad, el corte **solo se aplica cuando el dispositivo reporta velocidad
0** — es el propio firmware el que decide el momento, nunca el servidor a la
fuerza, para no dejar un vehículo en movimiento sin combustible. El dispositivo confirma un comando pendiente mandando
`acknowledged_command_id` en su siguiente lectura de telemetría (`POST /devices/{truck_id}/telemetry`); si en ese mismo
request la velocidad no es prácticamente 0, la confirmación se ignora aunque el dispositivo la haya mandado.

## Carta porte

`CartaPorteRecord` guarda los datos de cada viaje como **registro interno del sistema** — no es el CFDI de Carta Porte
timbrado ante el SAT, eso queda fuera de alcance del reto. Sí sigue la estructura del complemento oficial (un registro
por viaje, sin listas de mercancías/ubicaciones/remolques múltiples):

- Datos fiscales generales (RFC emisor/receptor, tipo de CFDI)
- Ubicación de origen y de destino (domicilio completo, clave, fecha/hora)
- Mercancía (clave SAT, descripción, pesos, material peligroso)
- Medio de transporte (config. vehicular, placas, permiso SICT, seguro)
- Figura de transporte / operador (nombre, RFC, licencia, domicilio)

Se captura y edita desde el panel de empleados (`/empleados`). Desde el panel de administración (`/panel`) se puede
descargar como PDF con el formato tradicional impreso:

```
GET /trips/{trip_id}/carta-porte/pdf
```

## Variables de entorno

Además de lo que ya tengas en `.env.example`, agrega:

| Variable | Para qué |
|---|---|
| `ENVIRONMENT` | Debe ser `production` en Render/producción — si no, el backend usa un atajo de desarrollo (`Base.metadata.create_all`) que crea tablas por fuera de Alembic y puede desincronizar el esquema |
| `EMPLOYEE_USERNAME` / `EMPLOYEE_PASSWORD` | Credenciales compartidas para el panel de empleados. **No dejar los valores por defecto en producción** |

## Despliegue en Render

El `Dockerfile` corre las migraciones antes de arrancar el servidor:

```dockerfile
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

Render **no usa `docker-compose.yml`** — solo el `Dockerfile`. Si en el dashboard de Render tiene algo escrito en
**Settings → Start Command**, eso sobreescribe el `CMD` de arriba; déjalo vacío o replica el mismo comando ahí.

## Pruebas

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest --cov=app --cov-report=term-missing
```

Las pruebas corren contra SQLite en memoria (ver `tests/conftest.py`, que usa `StaticPool` para compartir una sola
conexión entre el fixture de setup y las peticiones HTTP), así no dependen de tener Postgres corriendo para el CI.

## CI  
[![CI](https://github.com/Choclititito/FlotaTrack-EDSIA/.github/workflows/ci.yml)](https://github.com/Choclititito/FlotaTrack-EDSIA/actions)
