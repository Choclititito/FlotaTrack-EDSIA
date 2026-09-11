"""Simulador de dispositivo ESP32 para probar el backend sin hardware real.

Uso:
    pip install requests
    python scripts/simulate_device.py --truck-id <ID_DEL_CAMION>
"""

import argparse
import random
import time

import requests


def run(base_url: str, truck_id: str, interval: float) -> None:
    lat, lon = 19.5438, -96.9102  # Xalapa, Veracruz, como punto de partida
    fuel = 100.0
    speed = 0.0
    acknowledged_command_id: str | None = None

    print(f"Simulando telemetría para el camión {truck_id}. Ctrl+C para detener.")

    while True:
        lat += random.uniform(-0.001, 0.001)
        lon += random.uniform(-0.001, 0.001)
        speed = max(0.0, min(100.0, speed + random.uniform(-10, 10)))
        fuel = max(0.0, fuel - random.uniform(0.05, 0.2))

        payload = {
            "latitude": lat,
            "longitude": lon,
            "speed_kmh": round(speed, 1),
            "fuel_level_pct": round(fuel, 1),
        }
        if acknowledged_command_id:
            payload["acknowledged_command_id"] = acknowledged_command_id # type: ignore[assignment]
            acknowledged_command_id = None

        response = requests.post(
            f"{base_url}/devices/{truck_id}/telemetry", json=payload, timeout=5
        )
        response.raise_for_status()
        data = response.json()
        print(f"Enviado: {payload} -> pendiente: {data.get('pending_command')}")

        pending = data.get("pending_command")
        if pending and speed == 0.0:
            print(f"Aplicando comando '{pending['type']}' (vehículo detenido)...")
            acknowledged_command_id = pending["command_id"]

        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--truck-id", required=True)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--interval", type=float, default=5.0)
    args = parser.parse_args()
    run(args.base_url, args.truck_id, args.interval)
