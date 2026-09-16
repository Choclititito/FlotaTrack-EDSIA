def _create_truck(client):
    resp = client.post(
        "/trucks",
        json={"plates": "TEL-001", "model": "Kenworth T680", "capacity_kg": 20000},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _request_lock(client, truck_id):
    resp = client.post(
        f"/trucks/{truck_id}/kill-switch",
        json={"action": "lock", "confirm": True},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def test_telemetry_without_pending_command_has_no_pending_command(client):
    truck_id = _create_truck(client)

    resp = client.post(
        f"/devices/{truck_id}/telemetry",
        json={"latitude": 19.5, "longitude": -96.9, "speed_kmh": 80, "fuel_level_pct": 90},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["received"] is True
    assert body["pending_command"] is None


def test_telemetry_reports_pending_command_to_device(client):
    truck_id = _create_truck(client)
    command_id = _request_lock(client, truck_id)

    resp = client.post(
        f"/devices/{truck_id}/telemetry",
        json={"latitude": 19.5, "longitude": -96.9, "speed_kmh": 60, "fuel_level_pct": 90},
    )

    assert resp.status_code == 200
    pending = resp.json()["pending_command"]
    assert pending == {"type": "lock", "command_id": command_id}


def test_kill_switch_confirmation_ignored_while_moving(client):
    """El backend revalida velocidad de forma independiente (ADR-0002):
    si el dispositivo confirma pero va en movimiento, se ignora."""
    truck_id = _create_truck(client)
    command_id = _request_lock(client, truck_id)

    resp = client.post(
        f"/devices/{truck_id}/telemetry",
        json={
            "latitude": 19.5,
            "longitude": -96.9,
            "speed_kmh": 40,
            "fuel_level_pct": 90,
            "acknowledged_command_id": command_id,
        },
    )

    assert resp.status_code == 200
    assert resp.json()["pending_command"] == {"type": "lock", "command_id": command_id}

    truck = client.get("/trucks").json()[0]
    assert truck["security_state"] == "active"

    commands = client.get(f"/trucks/{truck_id}/commands").json()
    assert commands[0]["status"] == "pending"
    assert commands[0]["applied_at"] is None


def test_kill_switch_applied_when_stopped_and_confirmed(client):
    truck_id = _create_truck(client)
    command_id = _request_lock(client, truck_id)

    resp = client.post(
        f"/devices/{truck_id}/telemetry",
        json={
            "latitude": 19.5,
            "longitude": -96.9,
            "speed_kmh": 0,
            "fuel_level_pct": 90,
            "acknowledged_command_id": command_id,
        },
    )

    assert resp.status_code == 200
    assert resp.json()["pending_command"] is None

    truck = client.get("/trucks").json()[0]
    assert truck["security_state"] == "locked"

    commands = client.get(f"/trucks/{truck_id}/commands").json()
    assert commands[0]["status"] == "applied"
    assert commands[0]["applied_at"] is not None


def test_kill_switch_unlock_restores_active_state(client):
    truck_id = _create_truck(client)
    lock_id = _request_lock(client, truck_id)
    client.post(
        f"/devices/{truck_id}/telemetry",
        json={
            "latitude": 19.5,
            "longitude": -96.9,
            "speed_kmh": 0,
            "fuel_level_pct": 90,
            "acknowledged_command_id": lock_id,
        },
    )

    unlock_resp = client.post(
        f"/trucks/{truck_id}/kill-switch",
        json={"action": "unlock", "confirm": True},
    )
    unlock_id = unlock_resp.json()["id"]

    resp = client.post(
        f"/devices/{truck_id}/telemetry",
        json={
            "latitude": 19.5,
            "longitude": -96.9,
            "speed_kmh": 0,
            "fuel_level_pct": 90,
            "acknowledged_command_id": unlock_id,
        },
    )

    assert resp.status_code == 200
    truck = client.get("/trucks").json()[0]
    assert truck["security_state"] == "active"
