# Documentación de Protocolos de Multímetros - DMMView

Esta carpeta contiene las especificaciones de los protocolos de comunicación soportados por **DMMView**, con el objetivo de facilitar el mantenimiento y la extensión de la aplicación por otros desarrolladores.

## Contenido de la Documentación:

1. **[VICTOR 98A+](protocol_victor98a.md)**: Protocolo serie binario DMMVIEW_G (26 bytes).
2. **[OWON XDM Series](protocol_owon.md)**: Comandos ASCII estandarizados SCPI sobre puerto serie virtual.
3. **[UNI-T UT-61E+](protocol_ut61eplus.md)**: Protocolo binario sobre puente USB HID CP2110 (19 bytes).
4. **[UNI-T UT-181A](protocol_ut181.md)**: Inicialización del chip USB HID CP2110.
5. **[Brymen BM250s](protocol_brymen250.md)**: Transmisión unidireccional y decodificación de segmentos de pantalla LCD (15 bytes).
6. **[EEVBlog 121GW](protocol_eevblog121gw.md)**: Protocolo binario Bluetooth Low Energy (19 bytes).
7. **[Guía de Desarrollo](development_guide.md)**: Estructura del software, arquitectura en capas, flujos de hilos (Threading) y guía para crear nuevos plugins.
