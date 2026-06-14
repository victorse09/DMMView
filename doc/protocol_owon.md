# Protocolo de Comunicación - OWON XDM Series

Los multímetros de mesa OWON (XDM1041, XDM1241, XDM3041, XDM3051) utilizan comandos estandarizados **SCPI** (Standard Commands for Programmable Instruments) sobre un puerto serie virtual (USB CDC).

## Parámetros del Puerto Serie
* **Baudrate:** 9600 o 115200 (según configuración del multímetro)
* **Data Bits:** 8
* **Stop Bits:** 1
* **Paridad:** Ninguna (N)

## Flujo de Trabajo SCPI Común
Los comandos SCPI se envían en ASCII finalizados con un carácter de salto de línea `\n` (LF) o retorno de carro `\r`.

### Comandos de Control Principales:
* `*IDN?` - Solicita la identificación del multímetro (Retorna fabricante, modelo, número de serie y versión de firmware).
* `SYST:REM` - Pone el equipo en modo remoto para habilitar el control por software.
* `SYST:LOC` - Devuelve el equipo al modo de control local (panel físico).

### Comandos de Configuración y Lectura:
* `CONF:VOLT:DC` - Configura el equipo para medir tensión en CC.
* `CONF:VOLT:AC` - Configura el equipo para medir tensión en CA.
* `CONF:CURR:DC` - Configura el equipo para medir corriente en CC.
* `CONF:CURR:AC` - Configura el equipo para medir corriente en CA.
* `CONF:RES` - Configura la función de resistencia (2 hilos).
* `CONF:FRES` - Configura la función de resistencia (4 hilos, en modelos compatibles como XDM3041).
* `CONF:CAP` - Configura la función de capacitancia.
* `CONF:FREQ` - Configura la función de frecuencia.
* `CONF:DIOD` - Configura la prueba de diodos.
* `CONF:CONT` - Configura la prueba de continuidad.
* `CONF:TEMP` - Configura la medición de temperatura.

### Lectura de Mediciones:
* `MEAS?` - Realiza una lectura inmediata (configura por defecto e inicia la medición).
* `READ?` - Solicita el valor actual de la magnitud que el equipo tenga seleccionada. Retorna una cadena de texto en formato científico, ej: `+1.234567E+00`.
