def test_create_truck_and_ingest_telemetry(client):
    create_resp = client.post(
        "/trucks",
        json={"plates": "ABC-123", "model": "Kenworth T680", "capacity_kg": 20000},
    )
    assert create_resp.status_code == 201
    truck = create_resp.json()
    truck_id = truck["id"]
    assert truck["security_state"] == "active"

    telemetry_resp = client.post(
        f"/devices/{truck_id}/telemetry",
        json={
            "latitude": 19.5438,
            "longitude": -96.9102,
            "speed_kmh": 80.0,
            "fuel_level_pct": 75.5,
        },
    )
    assert telemetry_resp.status_code == 200
    body = telemetry_resp.json()
    assert body["received"] is True
    assert body["pending_command"] is None

    status_resp = client.get(f"/trucks/{truck_id}/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["latest_reading"]["speed_kmh"] == 80.0


def test_kill_switch_requires_confirmation(client):
    create_resp = client.post("/trucks", json={"plates": "XYZ-001", "model": "Volvo VNL"})
    truck_id = create_resp.json()["id"]

    resp = client.post(
        f"/trucks/{truck_id}/kill-switch", json={"action": "lock", "confirm": False}
    )
    assert resp.status_code == 400


def test_kill_switch_full_flow(client):
    create_resp = client.post("/trucks", json={"plates": "XYZ-999", "model": "Freightliner "})
    truck_id = create_resp.json()["id"]

    resp = client.post(f"/trucks/{truck_id}/kill-switch", json={"action": "lock", "confirm": True})
    assert resp.status_code == 201
    command_id = resp.json()["id"]
    assert resp.json()["status"] == "pending"

    # El dispositivo ve el comando pendiente en su siguiente lectura normal.
    telemetry_resp = client.post(
        f"/devices/{truck_id}/telemetry",
        json={"latitude": 19.0, "longitude": -96.0, "speed_kmh": 0.0, "fuel_level_pct": 50.0},
    )
    pending = telemetry_resp.json()["pending_command"]
    assert pending is not None
    assert pending["command_id"] == command_id

    # El dispositivo confirma que ya aplicó el corte (solo lo hace si iba a 0 km/h).
    ack_resp = client.post(
        f"/devices/{truck_id}/telemetry",
        json={
            "latitude": 19.0,
            "longitude": -96.0,
            "speed_kmh": 0.0,
            "fuel_level_pct": 50.0,
            "acknowledged_command_id": command_id,
        },
    )
    assert ack_resp.json()["pending_command"] is None

    status_resp = client.get(f"/trucks/{truck_id}/status")
    assert status_resp.json()["truck"]["security_state"] == "locked"


def test_new_command_cancels_previous_pending_one(client):
    create_resp = client.post("/trucks", json={"plates": "AAA-111", "model": "Volvo VNL"})
    truck_id = create_resp.json()["id"]

    # Se pide un "lock" pero nunca se confirma (se queda pendiente, como si el
    # dispositivo hubiera perdido señal).
    first = client.post(f"/trucks/{truck_id}/kill-switch", json={"action": "lock", "confirm": True})
    first_id = first.json()["id"]

    # Se pide un "unlock" antes de que el anterior se resuelva.
    second = client.post(
        f"/trucks/{truck_id}/kill-switch", json={"action": "unlock", "confirm": True}
    )
    second_id = second.json()["id"]

    telemetry_resp = client.post(
        f"/devices/{truck_id}/telemetry",
        json={"latitude": 19.0, "longitude": -96.0, "speed_kmh": 0.0, "fuel_level_pct": 50.0},
    )
    pending = telemetry_resp.json()["pending_command"]

    # El pendiente debe ser el segundo (el más reciente), nunca el primero.
    assert pending["command_id"] == second_id
    assert pending["command_id"] != first_id


def test_acknowledgement_ignored_if_still_moving(client):
    create_resp = client.post("/trucks", json={"plates": "BBB-222", "model": "Kenworth T680"})
    truck_id = create_resp.json()["id"]

    cmd_resp = client.post(
        f"/trucks/{truck_id}/kill-switch", json={"action": "lock", "confirm": True}
    )
    command_id = cmd_resp.json()["id"]

    # El dispositivo manda el acknowledged_command_id pero SIGUE en movimiento:
    # el servidor debe ignorar la confirmación, sin importar lo que diga el
    # dispositivo.
    telemetry_resp = client.post(
        f"/devices/{truck_id}/telemetry",
        json={
            "latitude": 19.0,
            "longitude": -96.0,
            "speed_kmh": 60.0,
            "fuel_level_pct": 50.0,
            "acknowledged_command_id": command_id,
        },
    )
    pending = telemetry_resp.json()["pending_command"]
    assert pending is not None
    assert pending["command_id"] == command_id  # sigue pendiente, no se aplicó

    status_resp = client.get(f"/trucks/{truck_id}/status")
    assert status_resp.json()["truck"]["security_state"] == "active"  # no cambió
