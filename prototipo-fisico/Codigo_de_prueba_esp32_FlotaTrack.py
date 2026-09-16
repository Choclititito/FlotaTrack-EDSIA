import time

import network
import urequests
from machine import UART, Pin

# ============================================================
# CONFIGURACION - AJUSTA ESTOS VALORES
# ============================================================
# Estas constantes son las que normalmente cambian de un camion/despliegue
# a otro. Se dejan arriba del todo para no tener que buscar dentro del
# codigo cada vez que se configura una nueva unidad.

WIFI_SSID = "WIFINOMBRE"
WIFI_PASSWORD = "CONTRASEÑA"

API_URL_BASE = "URLUSADO"  # cambia por la IP/dominio real de tu backend
TRUCK_ID = "ID DEL CAMION QUE SE VA A USAR"

INTERVALO_ENVIO = 15  # segundos entre cada envio al backend

# Calibracion del sensor ultrasonico segun tu tanque
# (distancia del sensor a la superficie del combustible, en cm)
# Estos dos valores se miden fisicamente en el tanque real:
# - con el tanque vacio, cuanto marca el sensor
# - con el tanque lleno, cuanto marca el sensor
# El calculo de porcentaje interpola linealmente entre estos dos extremos.
DISTANCIA_TANQUE_VACIO = 40.0   # cm cuando el tanque esta vacio
DISTANCIA_TANQUE_LLENO = 5.0    # cm cuando el tanque esta lleno

# Pines fisicos del ESP32 usados por cada periferico
PIN_GPS_RX = 16   # pin del ESP32 que RECIBE datos (se conecta al TX del GPS)
PIN_GPS_TX = 17   # pin del ESP32 que TRANSMITE datos (se conecta al RX del GPS)
PIN_TRIG = 5      # pin de disparo del sensor ultrasonico (salida)
PIN_ECHO = 18     # pin de eco del sensor ultrasonico (entrada)
PIN_LED = 4       # LED indicador: encendido = motor deshabilitado (kill switch activo)

# ============================================================
# INICIALIZACION DE PERIFERICOS
# ============================================================
# Se crean los objetos de hardware una sola vez, al arrancar el script,
# y se reutilizan durante todo el ciclo de vida del programa.

# UART 2 del ESP32 dedicado exclusivamente al modulo GPS, a 9600 baudios
# (velocidad estandar de los modulos GY-GPS6MV2).
gps = UART(2, baudrate=9600, tx=PIN_GPS_TX, rx=PIN_GPS_RX)

trig = Pin(PIN_TRIG, Pin.OUT)  # el ESP32 envia el pulso de disparo
echo = Pin(PIN_ECHO, Pin.IN)   # el ESP32 escucha cuanto tarda en volver el eco

led = Pin(PIN_LED, Pin.OUT)
led.value(0)  # arranca apagado (motor habilitado) por seguridad al encender


# ============================================================
# WIFI
# ============================================================

def conectar_wifi():
    """
    Conecta el ESP32 a la red WiFi configurada arriba.
    Devuelve True si logro conectarse, False si no.
    """
    wlan = network.WLAN(network.STA_IF)

    # Reinicia el estado del adaptador antes de conectar, evita el
    # "Wifi Internal State Error" que deja al driver en un estado invalido
    # (bug conocido del ESP32 cuando el WiFi queda en un estado raro tras
    # un reset o una desconexion previa).
    wlan.active(False)
    time.sleep(1)
    wlan.active(True)
    time.sleep(1)

    if not wlan.isconnected():
        print("Conectando a WiFi...")
        try:
            wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        except OSError as e:
            # connect() puede lanzar error si el adaptador sigue en mal estado
            print("Error al iniciar conexion WiFi:", e)
            return False

        # Espera activa hasta 20 segundos (40 intentos x 0.5s) a que conecte
        intentos = 0
        while not wlan.isconnected() and intentos < 40:
            time.sleep(0.5)
            intentos += 1

    if wlan.isconnected():
        print("WiFi conectado:", wlan.ifconfig()[0])
        return True
    else:
        print("No se pudo conectar a WiFi (revisa que la red sea de 2.4GHz)")
        return False


# ============================================================
# SENSOR ULTRASONICO (NIVEL DE COMBUSTIBLE)
# ============================================================

def medir_distancia_cm():
    """
    Dispara el sensor ultrasonico (pulso de 10us en TRIG) y mide el tiempo
    que tarda en volver el eco (ECHO) para calcular la distancia en cm.
    Devuelve None si no hubo respuesta a tiempo (timeout / sensor desconectado).
    """
    # Pulso de disparo: se asegura de que TRIG este bajo, se sube 10us y se
    # vuelve a bajar. Ese pulso es lo que hace que el sensor emita el sonido.
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    # Espera a que el echo suba (inicio del pulso de retorno).
    # Si pasan mas de 30ms sin respuesta, se asume que el sensor no contesto.
    timeout = time.ticks_us()
    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), timeout) > 30000:
            return None  # timeout, no hubo respuesta
    inicio = time.ticks_us()

    # Espera a que el echo baje otra vez (fin del pulso de retorno)
    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), inicio) > 30000:
            return None
    fin = time.ticks_us()

    # La duracion del pulso es proporcional al tiempo que el sonido tardo en
    # ir y volver. 0.0343 cm/us es la velocidad del sonido en el aire;
    # se divide entre 2 porque el sonido recorre la distancia dos veces
    # (ida hasta el liquido/superficie y vuelta hasta el sensor).
    duracion = time.ticks_diff(fin, inicio)
    distancia = (duracion * 0.0343) / 2
    return distancia


def calcular_porcentaje_combustible(distancia_cm):
    """
    Convierte la distancia medida (cm entre el sensor y la superficie del
    combustible) a un porcentaje de llenado del tanque, usando los valores
    de calibracion DISTANCIA_TANQUE_VACIO / DISTANCIA_TANQUE_LLENO.

    Logica: a mayor distancia, menos combustible (el nivel bajo hace que el
    sensor, montado arriba del tanque, quede mas lejos de la superficie).
    """
    if distancia_cm is None:
        return None

    rango = DISTANCIA_TANQUE_VACIO - DISTANCIA_TANQUE_LLENO
    porcentaje = (DISTANCIA_TANQUE_VACIO - distancia_cm) / rango * 100

    # Se limita el resultado entre 0 y 100 por si la medicion real cae
    # ligeramente fuera del rango calibrado (ruido del sensor, etc.)
    porcentaje = max(0, min(100, porcentaje))
    return round(porcentaje, 1)


# ============================================================
# LED INDICADOR (KILL SWITCH)
# ============================================================
# Nota: aqui el LED reemplaza al rele fisico. La logica es invertida
# respecto a "motor funcionando": LED encendido = motor deshabilitado.

def activar_motor():
    """Motor habilitado (kill switch desactivado): LED apagado."""
    led.value(0)
    print("Kill switch: motor habilitado")


def desactivar_motor():
    """Motor deshabilitado (kill switch activado): LED encendido."""
    led.value(1)
    print("Kill switch: motor deshabilitado")


# ============================================================
# GPS
# ============================================================

def convertir_a_decimal(valor_crudo, direccion):
    """
    Convierte una coordenada en formato NMEA crudo (grados y minutos
    pegados, ej. "1234.5678") a grados decimales (ej. 12.576...),
    aplicando el signo segun el hemisferio (N/S, E/W).
    """
    if not valor_crudo or valor_crudo == '':
        return None

    if direccion in ('E', 'W'):
        # La longitud usa 3 digitos para los grados (hasta 180)
        grados = int(valor_crudo[:3])
        minutos = float(valor_crudo[3:])
    else:
        # La latitud usa 2 digitos para los grados (hasta 90)
        grados = int(valor_crudo[:2])
        minutos = float(valor_crudo[2:])

    decimal = grados + (minutos / 60)

    # Sur y Oeste son negativos en el sistema de coordenadas decimal estandar
    if direccion in ('S', 'W'):
        decimal = -decimal

    return decimal


def parsear_gpgga(trama):
    """
    Parsea una trama NMEA $GPGGA (posicion y calidad del fix) y devuelve
    una tupla (lat, lon) en decimal, o None si la trama es invalida o
    todavia no hay fix satelital.
    """
    partes = trama.split(',')

    if len(partes) < 10:
        return None  # trama incompleta/corrupta

    # El campo 6 indica la calidad del fix: '0' significa "sin fix" todavia
    fix_quality = partes[6]
    if fix_quality == '0' or fix_quality == '':
        return None

    lat = convertir_a_decimal(partes[2], partes[3])
    lon = convertir_a_decimal(partes[4], partes[5])

    if lat is None or lon is None:
        return None

    return (lat, lon)


def parsear_gpvtg(trama):
    """
    Parsea una trama $GPVTG, que trae la velocidad sobre el suelo.
    El campo de velocidad en km/h es el 8vo (indice 7), justo antes de la 'K'.
    Formato: $GPVTG,rumbo,T,,,vel_nudos,N,vel_kmh,K*checksum
    """
    partes = trama.split(',')

    if len(partes) < 8:
        return None

    velocidad_cruda = partes[7]
    if not velocidad_cruda:
        return None

    try:
        return float(velocidad_cruda)
    except ValueError:
        return None


# Estado global del GPS: se van actualizando conforme llegan tramas nuevas,
# en vez de recalcularse cada vez, porque las tramas GPGGA y GPVTG llegan
# en momentos distintos dentro del mismo ciclo NMEA.
buffer_gps = ""
ultima_lat = None
ultima_lon = None
ultima_velocidad = 0.0


def actualizar_gps():
    """
    Lee todos los bytes disponibles del GPS, los acumula en un buffer propio,
    y procesa cada linea completa (terminada en salto de linea) que encuentre.

    Este buffer manual es necesario porque el UART puede entregar una trama
    NMEA "cortada" a la mitad si se lee en el momento equivocado; acumulando
    en 'buffer_gps' y esperando el '\\n' se garantiza procesar siempre
    lineas completas.

    Actualiza las variables globales ultima_lat, ultima_lon y ultima_velocidad
    conforme van llegando tramas GPGGA (posicion) y GPVTG (velocidad).
    """
    global buffer_gps, ultima_lat, ultima_lon, ultima_velocidad

    if gps.any():
        datos = gps.read()
        if datos:
            try:
                buffer_gps += datos.decode('utf-8', 'ignore')
            except Exception:
                # Si llega algun byte corrupto/no-UTF8 se ignora en vez de
                # tumbar el programa
                pass

    # Mientras haya al menos una linea completa en el buffer, se procesa.
    # split('\n', 1) separa la primera linea del resto, que se conserva
    # en buffer_gps para la siguiente vuelta.
    while '\n' in buffer_gps:
        linea, buffer_gps = buffer_gps.split('\n', 1)
        linea = linea.strip()

        if not linea:
            continue

        if linea.startswith('$GPGGA') or linea.startswith('$GNGGA'):
            resultado = parsear_gpgga(linea)
            if resultado:
                ultima_lat, ultima_lon = resultado

        elif linea.startswith('$GPVTG') or linea.startswith('$GNVTG'):
            velocidad = parsear_gpvtg(linea)
            if velocidad is not None:
                # Por debajo de 5 km/h se considera ruido de precision del GPS
                # (el modulo puede marcar 1-3 km/h aunque este completamente quieto)
                ultima_velocidad = velocidad if velocidad >= 5.0 else 0.0


# ============================================================
# ENVIO AL BACKEND
# ============================================================

# Guarda el id del comando (lock/unlock) que se debe confirmar en el
# SIGUIENTE envio HTTP, no en el mismo en el que se recibio.
ultimo_command_id_pendiente = ""


def enviar_lectura(lat, lon, velocidad, combustible):
    """
    Envia por HTTP POST la telemetria actual (posicion, velocidad,
    combustible) al backend, y procesa la respuesta para ver si el
    backend pidio activar o desactivar el kill switch.
    """
    global ultimo_command_id_pendiente

    url = f"{API_URL_BASE}/devices/{TRUCK_ID}/telemetry"

    payload = {
        "latitude": lat,
        "longitude": lon,
        "speed_kmh": velocidad,
        "fuel_level_pct": combustible,
        # Le avisa al backend cual fue el ultimo comando de kill switch que
        # ya se aplico, para que el backend pueda marcarlo como confirmado
        "acknowledged_command_id": ultimo_command_id_pendiente
    }

    try:
        respuesta = urequests.post(url, json=payload)
        print("Enviado. Status:", respuesta.status_code)

        if respuesta.status_code != 200 and respuesta.status_code != 201:
            print("Detalle del error:", respuesta.text)

        # El backend indica en la respuesta si hay un comando pendiente de
        # kill switch: {"received": true, "pending_command": {"type": "lock"|"unlock", "command_id": "..."}}
        try:
            data = respuesta.json()
            pendiente = data.get("pending_command")

            if pendiente and pendiente.get("type"):
                tipo = pendiente["type"]

                if tipo == "lock":
                    desactivar_motor()
                elif tipo == "unlock":
                    activar_motor()

                # Se guarda el id del comando que se acaba de aplicar; se
                # reconoce/confirma hasta el SIGUIENTE envio (arriba, en
                # 'acknowledged_command_id'), no en este mismo POST.
                ultimo_command_id_pendiente = pendiente.get("command_id", "")
            else:
                # No hay comando pendiente nuevo, no hay nada que reconocer
                ultimo_command_id_pendiente = ""
        except Exception:
            # Si la respuesta no trae JSON valido, simplemente no se procesa
            # el comando pendiente; la telemetria ya se envio de todas formas
            pass

        respuesta.close()
    except Exception as e:
        # Cubre errores de red (WiFi caido, backend inalcanzable, etc.)
        print("Error enviando datos:", e)


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():
    # Si no hay WiFi no tiene sentido seguir: no se podria reportar nada
    if not conectar_wifi():
        print("Sin WiFi, no se puede continuar")
        return

    global ultima_lat, ultima_lon, ultima_velocidad
    ultimo_envio = time.ticks_ms()
    ultimo_combustible_valido = 0.0  # respaldo por si el sensor falla

    while True:
        # Se vacia el buffer del GPS en CADA vuelta del loop (no solo cada
        # 15s) para no perder ni cortar tramas NMEA que llegan continuamente
        actualizar_gps()

        # Cada INTERVALO_ENVIO segundos, se mide combustible y se envia
        # todo el paquete de telemetria al backend
        if time.ticks_diff(time.ticks_ms(), ultimo_envio) > INTERVALO_ENVIO * 1000:
            distancia = medir_distancia_cm()
            combustible = calcular_porcentaje_combustible(distancia)

            if combustible is None:
                # El sensor fallo esta vez (timeout del pulso ultrasonico);
                # se reusa el ultimo valor valido en vez de mandar un dato
                # invalido (esto evita los errores 422 del backend)
                print("Lectura de combustible fallo, se reusa el ultimo valor valido")
                combustible = ultimo_combustible_valido
            else:
                ultimo_combustible_valido = combustible

            print("Lat:", ultima_lat, "Lon:", ultima_lon, "Vel:", ultima_velocidad, "km/h", "Combustible:", combustible, "%")

            if ultima_lat is not None and ultima_lon is not None:
                enviar_lectura(ultima_lat, ultima_lon, ultima_velocidad, combustible)
            else:
                # Sin fix de GPS todavia no se envia nada, para no mandar
                # coordenadas invalidas/nulas al backend
                print("Sin fix de GPS todavia, se omite el envio")

            ultimo_envio = time.ticks_ms()

        # Pequeña pausa para no saturar el CPU del ESP32 en el loop principal
        time.sleep_ms(5)


main()
