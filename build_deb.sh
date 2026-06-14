#!/bin/bash
# ==============================================================================
# Script para empaquetar DMMView como un instalador Debian (.deb)
# Generará: DMMView_3_3_1.deb
# ==============================================================================

set -e

# Nombre y versión del paquete
PKG_NAME="dmmview"
PKG_VERSION="3.3.1"
PKG_DIR="${PKG_NAME}_${PKG_VERSION}"
DIST_DIR="dist"
OUTPUT_DEB="${DIST_DIR}/DMMView_${PKG_VERSION}.deb"

echo "=== Iniciando empaquetado DEB para DMMView ==="
echo "Directorios de trabajo: $PKG_DIR"
echo "Archivo de salida: $OUTPUT_DEB"

# Asegurar que el directorio dist existe
mkdir -p "$DIST_DIR"

# Limpiar compilaciones anteriores
rm -rf "$PKG_DIR"
rm -f "$OUTPUT_DEB"

# Crear estructura de carpetas de Debian
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/dmmview"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/pixmaps"

# 1. Crear archivo de control DEBIAN
cat << EOF > "$PKG_DIR/DEBIAN/control"
Package: $PKG_NAME
Version: $PKG_VERSION
Section: utils
Priority: optional
Architecture: all
Maintainer: Victor <victorse09@github.com>
Depends: python3, python3-pyqt6, python3-matplotlib, python3-serial, python3-pip
Description: Digital Multimeter Viewer (DMMView)
 Aplicacion de visualizacion, registro de datos (logging) y analisis
 para multimetros digitales en Linux. Soporta marcas como VICTOR, Fluke,
 UNI-T, Brymen, EEVBlog y OWON.
EOF

# 2. Copiar archivos fuente del proyecto
echo "Copiando archivos fuente..."
cp dmmview.py "$PKG_DIR/usr/share/dmmview/"
cp dmmwin.py "$PKG_DIR/usr/share/dmmview/"
cp requirements.txt "$PKG_DIR/usr/share/dmmview/"
cp LEEME.TXT "$PKG_DIR/usr/share/dmmview/"
cp README.md "$PKG_DIR/usr/share/dmmview/"
cp screenshot.png "$PKG_DIR/usr/share/dmmview/"
cp -r core "$PKG_DIR/usr/share/dmmview/"
cp -r ui "$PKG_DIR/usr/share/dmmview/"
cp -r plugins "$PKG_DIR/usr/share/dmmview/"
cp -r doc "$PKG_DIR/usr/share/dmmview/"

# 3. Crear el script de arranque /usr/bin/dmmview
echo "Creando script ejecutable..."
cat << 'EOF' > "$PKG_DIR/usr/bin/dmmview"
#!/bin/bash
# Lanzador de DMMView
cd /usr/share/dmmview
python3 dmmview.py "$@"
EOF
chmod +x "$PKG_DIR/usr/bin/dmmview"

# 4. Configurar icono de la aplicacion
if [ -f "ui/icon.png" ]; then
    cp ui/icon.png "$PKG_DIR/usr/share/pixmaps/dmmview.png"
    chmod 644 "$PKG_DIR/usr/share/pixmaps/dmmview.png"
fi

# 5. Crear el acceso directo .desktop
cat << EOF > "$PKG_DIR/usr/share/applications/dmmview.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=DMMView
Comment=Digital Multimeter Viewer & Logger
Exec=dmmview
Icon=/usr/share/pixmaps/dmmview.png
Terminal=false
Categories=Utility;Development;Engineering;
Keywords=multimeter;dmm;logging;serial;
EOF

# 6. Compilar paquete DEB
echo "Construyendo el archivo .deb..."
dpkg-deb --build "$PKG_DIR" "$OUTPUT_DEB"

# Limpieza
rm -rf "$PKG_DIR"

echo "=== ¡Empaquetado Completo con Exito! ==="
echo "Se ha generado el archivo: $OUTPUT_DEB"
echo "Para instalarlo ejecuta: sudo dpkg -i $OUTPUT_DEB"
