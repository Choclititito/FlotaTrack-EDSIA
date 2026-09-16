# Documentación del Prototipo

> **Nota:** Este es un prototipo, diseñado únicamente para demostrar cómo sería el uso de este sistema en el futuro.

## Componentes del Sistema

El sistema está compuesto por el siguiente hardware:

- Microcontrolador **ESP32**
- Módulo GPS **GY-GPS6MV2** (NEO-6M)
- Sensor Ultrasónico **HC-SR04**
- Diodo Emisor de Luz (**LED**)

## Esquema de Conexiones

El circuito debe conectarse a los siguientes pines del ESP32:

| Componente | Pin del Componente | Pin del ESP32 |
| :--- | :--- | :--- |
| **LED** | Ánodo (Positivo) | `Pin 4` |
| **GPS GY-GPS6MV2** | RX | `Pin 17` |
| **GPS GY-GPS6MV2** | TX | `Pin 16` |
| **Sensor HC-SR04** | Trigger | `Pin 5` |
| **Sensor HC-SR04** | Echo | `Pin 18` |

*(Asegúrate de conectar las respectivas tierras (GND) y alimentaciones (VCC/3.3V/5V) de los módulos a los pines correspondientes del ESP32 o fuente de alimentación).*

## Hojas de Datos (Datasheets)

Para obtener información técnica detallada, consulta las hojas de datos de los módulos:

- [Datasheet - Módulo GPS NEO-6M (GY-GPS6MV2)](https://components101.com/sites/default/files/component_datasheet/NEO6MV2%20GPS%20Module%20Datasheet.pdf)
- [Datasheet - Sensor Ultrasónico HC-SR04](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf)