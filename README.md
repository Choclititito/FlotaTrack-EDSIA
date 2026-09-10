# FleetTrack — backend

Backend del sistema de monitoreo de flotilla (Reto Final EDSIA 2026): telemetría
(ubicación, velocidad, combustible), kill switch remoto antirrobo y registro de
carta porte por viaje.

## Stack

FastAPI + PostgreSQL + SQLAlchemy + Alembic, contenerizado con Docker.

## Cómo correrlo localmente

```bash
cp .env.example .env
docker compose up --build
```

La API queda en http://localhost:8000, con `/health` y `/docs` (Swagger UI).

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
fuerza, para no dejar un vehículo en movimiento sin combustible.

## Carta porte

`CartaPorteRecord` guarda los datos de cada viaje (folio, mercancía, peso,
configuración del transporte) como **registro interno del sistema** — no es el
CFDI de Carta Porte timbrado ante el SAT, eso queda fuera de alcance del reto.

## Pruebas

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest --cov=app --cov-report=term-missing
```

Las pruebas corren contra SQLite en memoria (ver `tests/conftest.py`), así no
dependen de tener Postgres corriendo para el CI.

## Qué falta (próximos pasos del backlog)

- Firmware real del ESP32: GPS + sensor de combustible + relé del kill switch,
  siguiendo el mismo protocolo que ya implementa `scripts/simulate_device.py`.
- Endpoints de conductores y viajes completos (los modelos ya están:
  `Driver`, `Trip`).
- Dashboard web (mapa en vivo + perfiles + historial de alertas).
- Experimento de detección de anomalías en combustible/ruta para el AI_LOG.
- Migrar el kill switch de "confirmación simple" a autenticación real de quién
  lo solicita.
