# Protocolo de Comunicación - UNI-T UT-181A

El multímetro de registro gráfico UNI-T UT-181A utiliza un puerto USB HID (Silicon Labs CP2110) similar al UT-61E+ para la transmisión de datos a una computadora de control.

## Conexión y Parámetros
* **Vendor ID (VID):** `0x10C4`
* **Product ID (PID):** `0xEA80`
* **Baudrate equivalente:** 9600 bps
* **Data Bits:** 8
* **Stop Bits:** 1
* **Paridad:** Ninguna (N)

## Configuración del Chip CP2110
1. Habilitar UART enviando el comando `0x41 0x01` mediante un Feature Report.
2. Configurar baudrate a 9600 mediante el reporte `0x50 0x00 0x00 0x25 0x80 0x00 0x00 0x03 0x00 0x00`.
3. Purgar FIFOs enviando `0x43 0x02`.
4. Leer bytes continuamente del reporte de entrada de datos HID.
