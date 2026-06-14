# Protocolo de Comunicación - EEVBlog 121GW

El multímetro EEVBlog 121GW transmite datos de forma inalámbrica a través de Bluetooth Low Energy (BLE) utilizando paquetes binarios estructurados de 19 bytes.

## UUIDs del Servicio BLE
* **Service UUID:** `0bd51666-e7cb-469b-8e4d-2742f1ba77cc`
* **Characteristic UUID:** `e7add780-b042-4876-aae1-112855353cc1` (Soporta notificaciones).

## Estructura del Paquete Binario (19 bytes)
Cuando se suscribe a las notificaciones, el multímetro envía un paquete de 19 bytes con la lectura del display principal, display secundario, barra analógica y estado general.

### Desglose del Paquete:
1. **Byte 0:** Banderas de estado del display principal (ej: Autorrango en `bit 1`).
2. **Byte 1:**
   * Bits 4-7: Código de la función/modo del display principal.
   * Bits 0-3: Código del rango del display principal.
3. **Bytes 2-4:** Valor principal de 20 bits con signo:
   * Byte 2 Bit 7: Bit de signo (1 para negativo, 0 para positivo).
   * Resto de bits de Byte 2, 3 y 4 representan la magnitud entera.
4. **Byte 5:** Número de decimales (posición de la coma) del display principal.
5. **Byte 6:** Banderas extra del display principal.
6. **Bytes 7-8:** Valor del display secundario (16 bits big-endian).
7. **Byte 9:** Código de la función/modo del display secundario (4 bits inferiores).
8. **Byte 10:** Información extra del display secundario.
9. **Byte 11:** Número de decimales y banderas del display secundario.
10. **Byte 12:** Estado del display secundario.
11. **Bytes 13-14:** Estado del gráfico de barras analógico.
12. **Bytes 15-17:** Banderas de estado general del multímetro.
13. **Byte 18:** Suma de comprobación (CRC/Sync).

### Tabla de Códigos de Funciones comunes (Bits 4-7 del Byte 1):
* `0`: Low Z V (Baja impedancia)
* `1`: DCV (Tensión de CC)
* `2`: ACV (Tensión de CA)
* `3`: DCmV (Tensión de CC en mV)
* `4`: ACmV (Tensión de CA en mV)
* `5`: Temp (Temperatura)
* `6`: Hz (Frecuencia)
* `7`: Duty% (Ciclo de trabajo)
* `8`: mA DC (Corriente mA CC)
* `14`: Diode (Diodos)
* `15`: Continuity (Continuidad)
* `16`: Resistencia (Ω)
* `17`: Capacitancia (F)
