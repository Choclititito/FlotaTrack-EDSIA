def _carta_porte_payload(**overrides):
    """ válido para CartaPorteCreate;usar para variar solo lo que le importa a cada test."""
    payload = {
        "folio": "CP-0001",
        "emisor_rfc": "AAA010101AAA",
        "receptor_rfc": "BBB020202BBB",
        "tipo_cfdi": "Traslado",
        "origen_clave": "30039",
        "origen_calle": "Av. Xalapa",
        "origen_colonia": "Centro",
        "origen_municipio": "Xalapa",
        "origen_estado": "Veracruz",
        "origen_codigo_postal": "91000",
        "origen_fecha_hora_salida": "2026-09-14T08:00:00",
        "destino_clave": "30370",
        "destino_calle": "Av. Juárez",
        "destino_colonia": "Centro",
        "destino_municipio": "Coatepec",
        "destino_estado": "Veracruz",
        "destino_codigo_postal": "91500",
        "destino_fecha_hora_llegada": "2026-09-14T09:30:00",
        "distancia_recorrida_km": 12.5,
        "mercancia_clave_prod_serv": "01010101",
        "merchandise_description": "Café en grano",
        "mercancia_peso_bruto_kg": 2000,
        "mercancia_peso_neto_kg": 1950,
        "mercancia_clave_unidad": "KGM",
        "config_vehicular": "C2",
        "placa_camion": "DDD-444",
        "numero_permiso_sict": "SICT-12345",
        "aseguradora_nombre": "Seguros Atlas",
        "poliza_numero": "POL-0001",
        "operador_nombre": "Carlos Ruiz",
        "operador_rfc": "CCC030303CCC",
        "operador_licencia": "LIC-CARLOS-01",
        "operador_domicilio": "Calle Falsa 123, Xalapa, Ver.",
    }
    payload.update(overrides)
    return payload


def test_create_driver(client):
    resp = client.post(
        "/drivers", json={"name": "Juan Pérez", "license_number": "LIC-001", "phone": "2281234567"}
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Juan Pérez"


def test_create_trip_requires_existing_truck_and_driver(client):
    # Sin camión ni conductor todavía: debe fallar con 404.
    resp = client.post(
        "/trips",
        json={
            "truck_id": "no-existe",
            "driver_id": "no-existe",
            "origin": "Xalapa",
            "destination": "Coatepec",
        },
    )
    assert resp.status_code == 404


def test_trip_full_flow_and_driver_history(client):
    truck_resp = client.post("/trucks", json={"plates": "CCC-333", "model": "Volvo VNL"})
    truck_id = truck_resp.json()["id"]

    driver_resp = client.post("/drivers", json={"name": "María López"})
    driver_id = driver_resp.json()["id"]

    trip_resp = client.post(
        "/trips",
        json={
            "truck_id": truck_id,
            "driver_id": driver_id,
            "origin": "Xalapa",
            "destination": "Coatepec",
            "cargo_description": "Café en grano, 2 toneladas",
        },
    )
    assert trip_resp.status_code == 201
    trip_id = trip_resp.json()["id"]

    detail_resp = client.get(f"/trips/{trip_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["origin"] == "Xalapa"

    history_resp = client.get(f"/drivers/{driver_id}/trips")
    assert history_resp.status_code == 200
    assert len(history_resp.json()) == 1
    assert history_resp.json()[0]["id"] == trip_id


def test_carta_porte_create_then_update(client, employee_auth):
    truck_resp = client.post("/trucks", json={"plates": "DDD-444", "model": "Kenworth T680"})
    truck_id = truck_resp.json()["id"]
    driver_resp = client.post("/drivers", json={"name": "Carlos Ruiz"})
    driver_id = driver_resp.json()["id"]
    trip_resp = client.post(
        "/trips",
        json={
            "truck_id": truck_id,
            "driver_id": driver_id,
            "origin": "Xalapa",
            "destination": "Veracruz",
        },
    )
    trip_id = trip_resp.json()["id"]

    # Primera vez: se crea (201). El endpoint requiere auth de empleado.
    create_resp = client.post(
        f"/trips/{trip_id}/carta-porte",
        json=_carta_porte_payload(folio="CP-0001"),
        auth=employee_auth,
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["folio"] == "CP-0001"

    # Segunda vez sobre el mismo viaje: se actualiza (200), no se duplica.
    update_resp = client.post(
        f"/trips/{trip_id}/carta-porte",
        json=_carta_porte_payload(
            folio="CP-0001-CORREGIDO",
            merchandise_description="Café en grano, tostado",
            mercancia_peso_bruto_kg=2100,
        ),
        auth=employee_auth,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["folio"] == "CP-0001-CORREGIDO"

    # El GET no requiere auth (ver get_carta_porte en trips.py).
    get_resp = client.get(f"/trips/{trip_id}/carta-porte")
    assert get_resp.status_code == 200
    assert get_resp.json()["mercancia_peso_bruto_kg"] == 2100


def test_carta_porte_not_found_before_registered(client):
    truck_resp = client.post("/trucks", json={"plates": "EEE-555", "model": "Kenworth T680"})
    truck_id = truck_resp.json()["id"]
    driver_resp = client.post("/drivers", json={"name": "Ana Torres"})
    driver_id = driver_resp.json()["id"]
    trip_resp = client.post(
        "/trips",
        json={
            "truck_id": truck_id,
            "driver_id": driver_id,
            "origin": "Xalapa",
            "destination": "Perote",
        },
    )
    trip_id = trip_resp.json()["id"]

    get_resp = client.get(f"/trips/{trip_id}/carta-porte")
    assert get_resp.status_code == 404