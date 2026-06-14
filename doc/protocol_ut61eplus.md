# Protocolo de Comunicación - UNI-T UT-61E+

El multímetro UNI-T UT-61E+ transmite datos en binario a través de un puente USB HID integrado (Silicon Labs CP2110).

## Conexión y Parámetros
* **Vendor ID (VID):** `0x10C4`
* **Product ID (PID):** `0xEA80`
* **Baudrate equivalente:** 9600 bps

Para iniciar la comunicación, el software envía un reporte de configuración (Feature Report) al CP2110 para habilitar la UART y configurar los parámetros a 9600 baudios, 8 bits de datos, 1 stop bit, sin paridad (8N1).

## Envío y Recepción de Comandos
El protocolo consiste en enviar tramas específicas para solicitar datos:
* **Comando para obtener datos:** `AB CD 03 5E 01 D9` (en hexadecimal).

## Estructura del Paquete de Medición (19 bytes)
El multímetro responde con un paquete binario que comienza con la cabecera `AB CD` y contiene los siguientes bytes:
1. **Header (2 bytes):** `AB CD`
2. **Longitud (1 byte):** Longitud del resto del paquete.
3. **Modo (1 byte):** Índice que determina la función (Tensión, Resistencia, etc. según la tabla `MODE_TABLE`).
4. **Rango (1 byte):** Índice de rango que determina la posición del punto decimal y el prefijo de la unidad.
5. **Valor de Medición (Cadena ASCII):** Dígitos en ASCII representando la lectura.
6. **Banderas de Estado (Bytes posteriores):** Indican modos adicionales (Autorrango, Máximo/Mínimo, etc.).
7. **Checksum (1 byte):** Byte final para control de errores de transmisión.
