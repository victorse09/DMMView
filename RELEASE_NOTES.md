# Release Notes - DMMView v3.3.1 (Official Release)

¡Bienvenido a la versión **3.3.1** de **DMMView**! Esta entrega consolida el soporte multiplataforma nativo (Linux y Windows), añade soporte para nuevos instrumentos y soluciona diversos detalles de visualización, calibración de rangos y detección de sobrecargas.

---

## 🚀 Novedades y Características Clave

### 1. Soporte Multiplataforma Completo
* **Windows 10/11:** Lanzador nativo `dmmwin.py` con tipografía `Segoe UI` y optimizaciones para pantallas de alta densidad de píxeles (DPI).
* **Linux (Debian/Ubuntu/Mint):** Lanzador `dmmview.py` optimizado que valida de forma automática los permisos del grupo `dialout` para puertos serie y HID.

### 2. Nuevos Multímetros Soportados
* **UNI-T UT-181A** (Conexión directa USB HID).
* **OWON XDM1041 / XDM1241** y **OWON XDM3041 / XDM3051** (Comandos estándar SCPI).

### 3. Correcciones Críticas para VICTOR 98A+
* **Detección de Sobrecarga (OL):** Se reescribió el parser de valores del protocolo para identificar tramas con signo (como `+FFFFFF`/`-FFFFFF`) en las funciones de Continuidad (`CONT`), Diodos y Resistencia (`OHM`), evitando que la barra analógica se quede vacía.
* **Escala VFC (Filtro de Paso Bajo):** Habilitada con la etiqueta `ACV~ VFC`, unidad `V`, modo AC activo y corrección de mapeo para rango de 1000V.
* **Unidades de Medición:** Corregida la unidad del valor terciario en modo `dBm` (muestra resistencia de referencia en `Ω`) y valor secundario de temperatura `RTD` (muestra la resistencia en `kΩ` en lugar de `mV`).
* **Rango de Continuidad:** Ajustado a `200Ω` (escala física real).

### 4. Empaquetado Automático y Documentación
* Scripts de automatización para generar instaladores independientes y portables: `.deb` (Debian/Ubuntu), `.flatpak` (Flatpak) y `.exe` (PyInstaller para Windows).
* Carpeta `doc/` con especificaciones de protocolos para futuros desarrolladores.

---

## 📦 Archivos Adjuntos (Assets)

### 🔹 `DMMView_3.3.1.deb` (Linux Debian / Ubuntu / Mint)
Instalador estándar para sistemas basados en Debian.
* **Instalación:**
  ```bash
  sudo dpkg -i DMMView_3.3.1.deb
  ```
* **Ejecución:** Búscalo en tu menú de aplicaciones como **DMMView** o ejecuta `dmmview` en la terminal.

### 🔹 `DMMView_3_3_1.flatpak` (Linux Universal)
Contenedor autocontenido que incluye todas las dependencias y librerías de Python de forma aislada.
* **Instalación:**
  ```bash
  flatpak install --user DMMView_3_3_1.flatpak
  ```
* **Ejecución:**
  ```bash
  flatpak run com.github.victorse09.dmmview
  ```

### 🔹 `DMMView3_3_0.exe` (Windows Portable)
Ejecutable portable compilado para Windows 10/11. No requiere instalación de Python ni dependencias locales.
* **Uso:** Haz doble clic sobre el archivo para iniciar la aplicación.
