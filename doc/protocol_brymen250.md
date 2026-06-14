# Protocolo de Comunicación - Brymen BM250s

El multímetro de mano Brymen BM250s transmite datos de forma unidireccional y continua a través de su puerto óptico infrarrojo (usando el cable de conexión BRUA-20X).

## Configuración y Parámetros
* **Baudrate:** 9600
* **Data Bits:** 8
* **Stop Bits:** 1
* **Paridad:** Ninguna (N)

*Nota:* Para habilitar la transmisión de datos ópticos en el instrumento físico, se debe presionar y mantener pulsada la tecla **HOLD** mientras se enciende el multímetro.

## Estructura de la Trama de Datos (15 bytes)
El multímetro transmite tramas binarias pasivas de 15 bytes a intervalos regulares. Las tramas siguen la siguiente estructura:

* **Byte 0:** Byte de inicio de trama (siempre `0x02`).
* **Byte 1:** Banderas de estado 1 (ej: indica si la medición es AC (`bit 3`), DC (`bit 2`) o Autorrango (`bit 1`)).
* **Byte 2:** Banderas de estado 2 (los 4 bits superiores definen la función actual y los 4 bits inferiores el rango de medición).
* **Bytes 3-10:** Estado de los segmentos del LCD (4 dígitos en total, representados en 2 bytes por dígito).
* **Bytes 11-12:** Estado de los segmentos del gráfico de barras analógico.
* **Bytes 13-14:** Checksum y fin de trama.

### Tabla de Modos de Medición (Byte 2 bits 4-7):
* `0x00`: DCV (Tensión de CC)
* `0x01`: ACV (Tensión de CA)
* `0x02`: DCA (Corriente de CC)
* `0x03`: ACA (Corriente de CA)
* `0x04`: OHM (Resistencia)
* `0x05`: CAP (Capacitancia)
* `0x06`: Hz (Frecuencia)
* `0x07`: DUTY (Ciclo de trabajo)
* `0x08`: °C (Temperatura Celsius)
* `0x0A`: DIODE (Prueba de diodos)
* `0x0B`: CONT (Continuidad)
* `0x0E`: DBM (dBm)
