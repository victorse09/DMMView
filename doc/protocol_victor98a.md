# Protocolo de Comunicación - VICTOR 98A+

El multímetro VICTOR 98A+ utiliza el protocolo propietario **DMMVIEW_G** sobre puerto serie (UART).

## Parámetros del Puerto Serie
* **Baudrate:** 9600
* **Data Bits:** 8
* **Stop Bits:** 1
* **Paridad:** Ninguna (N)

## Formato de los Comandos (Enviados de la PC al DMM)
Los comandos inician con `#` y finalizan con un retorno de carro `\r` (CR).
* `#ONL\r` - Conectar / Poner el dispositivo en línea.
* `#RST\r` - Reiniciar el dispositivo.
* `#RD?\r` - Solicitar lectura de datos en tiempo real.
* `#SELx\r` - Cambiar sub-función (donde `x` es el byte de sub-función).
* `#RANx1x2\r` - Cambiar rango. `x1` es `0x31` (Autorrango) o `0x30` (Manual). `x2` es el byte del rango deseado.
* `#SC?\r` - Leer el número de registros en la memoria manual del DMM.
* `#SD?xxxx\r` - Leer el registro manual número `xxxx` (4 dígitos decimales en ASCII, ej: `0005`).
* `#TC?\r` - Leer el número de registros en la memoria temporizada del DMM.
* `#TI?\r` - Leer el intervalo de muestreo configurado para la memoria temporizada.
* `#TD?xxxx\r` - Leer el registro temporizado número `xxxx`.

## Estructura de Respuesta del Multímetro
El DMM responde con paquetes de datos que tienen una cabecera según el comando y un payload de **26 bytes** que describe completamente el estado del multímetro y sus lecturas.

### Formato del Payload de Medición (26 bytes):
1. **Código de Función (2 bytes):** Define la magnitud física medida (ej: ACV, DCV, Resistencia, etc.).
2. **Código de Rango 1 (1 byte):** Rango de la medición principal.
3. **Datos 1 (7 bytes):** Cadena ASCII del valor principal (ej: `+00.000` o `FFFFFF` para sobrecarga).
4. **Código de Rango 2 (1 byte):** Rango de la medición secundaria.
5. **Datos 2 (7 bytes):** Cadena ASCII del valor secundario.
6. **Código de Rango 3 (1 byte):** Rango de la medición terciaria.
7. **Datos 3 (7 bytes):** Cadena ASCII del valor terciario.

### Códigos de Función Comunes (Primeros 2 bytes):
* `(0x30, 0x30)`: ACV (Tensión Alterna)
* `(0x30, 0x31)`: dBm_V (Medición en dBm basada en tensión)
* `(0x30, 0x34)`: DCV (Tensión Continua)
* `(0x30, 0x37)`: CONT (Continuidad)
* `(0x30, 0x38)`: DIODE (Prueba de diodos)
* `(0x30, 0x39)`: OHM (Resistencia)
* `(0x31, 0x31)`: CAP (Capacitancia)
* `(0x31, 0x32)`: FREQ (Frecuencia)
* `(0x33, 0x34)`: ACV~ VFC (Tensión de CA con filtro de paso bajo activo)

### Respuestas de Estado:
* **ACK:** `0x06 0x00` en respuesta a comandos exitosos.
* **NAK:** `0x15 0x00` en respuesta a comandos fallidos o no soportados en el modo actual.
