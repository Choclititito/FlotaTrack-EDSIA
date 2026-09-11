# Backlog — FleetTrack
> ✅ = ya implementado y probado · ⬜ = pendiente

---

## Sprint 1 (ya cubierto)

### E1 — Modelo de datos y API base
- ✅ HU: Como despachador, quiero registrar un camión, para tener un inventario de la flotilla
  - Modelo `Truck` + `POST /trucks` + `GET /trucks`
- ✅ HU: Como despachador, quiero ver el estado y última ubicación de un camión
  - `GET /trucks/{id}/status`
- ✅ HU: Como despachador, quiero registrar conductores
  - Modelo `Driver` + `POST /drivers` + `GET /drivers` + `GET /drivers/{id}`
- ✅ HU: Como despachador, quiero registrar viajes con origen, destino y carga
  - Modelo `Trip` + `POST /trips` + `GET /trips` + `GET /trips/{id}`
- ✅ HU: Como despachador, quiero ver el historial de viajes de un conductor
  - `GET /drivers/{id}/trips`

### E2 — Telemetría y seguridad
- ✅ HU: Como sistema, quiero recibir lecturas periódicas de telemetría de un camión
  - `POST /devices/{truck_id}/telemetry`
- ✅ HU: Como despachador, quiero poder bloquear/desbloquear remotamente un camión (antirrobo)
  - Modelo `Command` + protocolo completo de kill switch (el corte solo se aplica cuando el camión reporta velocidad ~0)
  - `POST /trucks/{id}/kill-switch`
- ✅ Simulador de dispositivo (`scripts/simulate_device.py`) para probar sin hardware real

### E5 — Piso profesional
- ✅ CI en GitHub Actions: ruff, mypy, pytest con cobertura ≥80%
- ✅ Dockerfile + docker-compose (un comando levanta todo)
- ✅ Migraciones con Alembic
- ✅ `/health` y `/docs` disponibles
- ✅ Tests corriendo contra SQLite en memoria (no dependen de Postgres en CI)

---

## Sprint 2 (en curso)

### E1 — Modelo de datos y API base
- [ ] HU: Como despachador, quiero registrar los datos de carta porte de un viaje
  - Prioridad: Must
  - Tareas: `POST /trips/{trip_id}/carta-porte`, `GET /trips/{trip_id}/carta-porte`, validar folio único, tests
- [ ] HU: Como despachador, quiero marcar un viaje como finalizado
  - Prioridad: Must
  - Tareas: `PATCH /trips/{trip_id}/finish`, regla para no finalizar dos veces, tests

### E3 — Detección de anomalías
- [ ] HU: Como despachador, quiero recibir una alerta cuando el combustible cae de forma anómala respecto a la distancia recorrida
  - Prioridad: Must
  - Tareas: definir umbral/regla, servicio de detección, modelo de alertas, endpoint de consulta, tests
  - Nota para AI_LOG: documentar los supuestos de la regla (consumo esperado por km, margen de tolerancia) y que quedan pendientes de calibrar con datos reales

### E5 — Piso profesional
- [ ] ⚠️ Mover usuario/contraseña de Postgres en `docker-compose.yml` a variables de entorno (hoy están hardcodeados — viola la regla de "cero secretos")
  - Prioridad: Must, antes de la Compuerta 2
- [ ] HU: Como equipo, queremos el servicio desplegado en producción con `/health` y `/docs` accesibles
  - Prioridad: Must
  - Tareas: elegir proveedor, configurar CD, evidencia de que un commit actualiza producción

---

## Sprint 3

### E2 — Telemetría y seguridad
- [ ] HU: Como despachador, quiero que el kill switch requiera autenticación real de quién lo solicita
  - Prioridad: Must
  - Tareas: esquema de auth (API key/JWT), proteger el endpoint, registrar quién solicitó cada comando
- [ ] HU: Como auditor, quiero un registro de quién solicitó cada bloqueo/desbloqueo
  - Prioridad: Should
- [ ] Tarea: firmware real del ESP32 (GPS + sensor de combustible + relé), siguiendo el protocolo del simulador
  - Prioridad: Should — da sello de innovación si se logra

### E3 — Detección de anomalías
- [ ] HU: Como despachador, quiero recibir una alerta cuando un camión se desvía de la ruta esperada
  - Prioridad: Should
  - Tareas: definir qué es "ruta esperada", lógica de desviación, tests

### E4 — Dashboard / consulta
- [ ] HU: Como despachador, quiero ver un mapa con la ubicación en vivo de toda mi flotilla
  - Prioridad: Must
  - Tareas: integrar Mapbox GL JS, token en variable de entorno (MAPBOX_ACCESS_TOKEN), un marcador por camión usando lat/lon ya disponibles en la API. Ver ADR-0003
- [ ] HU: Como despachador, quiero ver el estado de seguridad de cada camión y accionar el kill switch desde el dashboard
  - Prioridad: Should
  - Tareas: endpoint de geocodificación inversa en el backend (Mapbox Geocoding API), caché simple por coordenada redondeada para no gastar cuota, test con la llamada externa mockeada. Ver ADR-0003
- [ ] HU: Como despachador o conductor, quiero consultar el perfil de un camión/conductor con su historial
  - Prioridad: Should
- [ ] HU: Como despachador, quiero ver las alertas de anomalías activas en el dashboard
  - Prioridad: Should (depende de E3)
- [ ] HU: Como despachador, quiero filtrar viajes por camión, conductor o estado
  - Prioridad: Could

### E5 — Piso profesional
- [ ] Agregar badge de CI y URL de producción al README
  - Prioridad: Must


### E6 — Documentación y entrega
- [ ] README como portada del producto (qué es, para quién, cómo se usa, URL de producción, badge de CI)
- [ ] ADRs de decisiones clave (ej. protocolo del kill switch, por qué SQLite en tests vs Postgres en producción)
- [ ] AI_LOG con criterio de uso de IA (qué se pidió, qué se aceptó, qué se rechazó y por qué)
- [ ] One-pager ejecutivo (una cuartilla)
- [ ] Documentacion del diseño del circuito
- [ ] Documentacion del sistema 
- [ ] Licencia de uso y documentacion de las APIs externas utilizadas
- [ ] Video de presentación (máx. 10 min, demo real sobre producción, los 3 integrantes)
- [ ] Congelar código antes del cierre

---

## Fuera de alcance (Won't — esta vez)

- [ ] App móvil para conductores
- [ ] Generación del CFDI de Carta Porte timbrado ante el SAT (hoy solo se guarda el registro interno)
- [ ] Mapa tridimensional  
- [ ] Ubicacion por satelite 
- [ ] Optimizacion del hardware
- [ ] Sensores y actuadores especializados 
- [ ] Cambio a APIs, con mayor capacidad de request y de uso comercial