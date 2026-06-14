#!/bin/bash
# ==============================================================================
# Script para compilar y empaquetar DMMView usando Flatpak
# ==============================================================================

set -e

MANIFEST="com.github.victorse09.dmmview.yaml"
BUILD_DIR="flatpak_build"
EXPORT_REPO="flatpak_repo"
DIST_DIR="dist"
BUNDLE_FILE="${DIST_DIR}/DMMView_3_3_1.flatpak"

echo "=== Iniciando construcción Flatpak para DMMView ==="

# Verificar si flatpak-builder está instalado
if ! command -v flatpak-builder &> /dev/null; then
    echo "[ERROR] 'flatpak-builder' no está instalado en el sistema."
    echo "Puedes instalarlo con: sudo apt install flatpak-builder"
    exit 1
fi

# Asegurar que el directorio dist existe
mkdir -p "$DIST_DIR"

# Limpiar carpetas anteriores
rm -rf "$BUILD_DIR"
rm -rf "$EXPORT_REPO"
rm -f "$BUNDLE_FILE"

# Compilar la aplicación usando el manifiesto
echo "[1/3] Compilando la aplicación con flatpak-builder..."
flatpak-builder --force-clean "$BUILD_DIR" "$MANIFEST"

# Crear un repositorio de exportación temporal y exportar la compilación
echo "[2/3] Exportando compilación al repositorio Flatpak..."
flatpak-builder --export-only --repo="$EXPORT_REPO" "$BUILD_DIR" "$MANIFEST"

# Generar el archivo bundle .flatpak portable
echo "[3/3] Generando el paquete bundle portable: $BUNDLE_FILE..."
flatpak build-bundle "$EXPORT_REPO" "$BUNDLE_FILE" com.github.victorse09.dmmview --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo

# Limpieza
rm -rf "$BUILD_DIR"
rm -rf "$EXPORT_REPO"

echo "=== ¡Construcción Flatpak Completada con Éxito! ==="
echo "Se ha generado el archivo: $BUNDLE_FILE"
echo ""
echo "Para instalar el paquete generado ejecuta:"
echo "  flatpak install --user $BUNDLE_FILE"
echo ""
echo "Para correr la aplicación una vez instalada:"
echo "  flatpak run com.github.victorse09.dmmview"
