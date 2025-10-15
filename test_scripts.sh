#!/bin/bash

# Scripts de prueba para el servidor OCR
# Asegúrate de tener curl instalado

SERVER_URL="http://localhost:5050"

echo "🧪 Scripts de prueba para OCR Server"
echo "=================================="

# Función para probar salud del servicio
test_health() {
    echo "📍 Probando endpoint de salud..."
    curl -s "$SERVER_URL/health" | python3 -m json.tool
    echo -e "\n"
}

# Función para probar OCR con imagen
test_image_ocr() {
    if [ -z "$1" ]; then
        echo "❌ Error: Proporciona la ruta de la imagen"
        echo "Uso: test_image_ocr /ruta/a/imagen.jpg"
        return 1
    fi
    
    echo "📄 Probando OCR con imagen: $1"
    curl -s -F "file=@$1" -F "lang=spa+eng" "$SERVER_URL/ocr" | python3 -m json.tool
    echo -e "\n"
}

# Función para probar OCR con PDF
test_pdf_ocr() {
    if [ -z "$1" ]; then
        echo "❌ Error: Proporciona la ruta del PDF"
        echo "Uso: test_pdf_ocr /ruta/a/documento.pdf"
        return 1
    fi
    
    echo "📄 Probando OCR con PDF: $1"
    curl -s -F "file=@$1" -F "lang=spa+eng" -F "optimize=1" -F "deskew=1" -F "clean=1" "$SERVER_URL/ocr" | python3 -m json.tool
    echo -e "\n"
}

# Función para probar diferentes idiomas
test_languages() {
    if [ -z "$1" ]; then
        echo "❌ Error: Proporciona la ruta del archivo"
        echo "Uso: test_languages /ruta/a/archivo.pdf"
        return 1
    fi
    
    echo "🌍 Probando diferentes idiomas con: $1"
    
    echo "--- Español ---"
    curl -s -F "file=@$1" -F "lang=spa" "$SERVER_URL/ocr" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Páginas: {data.get(\"pages\", \"N/A\")}, Texto (primeros 100 chars): {data.get(\"text\", \"\")[:100]}...')"
    
    echo "--- Inglés ---"
    curl -s -F "file=@$1" -F "lang=eng" "$SERVER_URL/ocr" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Páginas: {data.get(\"pages\", \"N/A\")}, Texto (primeros 100 chars): {data.get(\"text\", \"\")[:100]}...')"
    
    echo "--- Español + Inglés ---"
    curl -s -F "file=@$1" -F "lang=spa+eng" "$SERVER_URL/ocr" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Páginas: {data.get(\"pages\", \"N/A\")}, Texto (primeros 100 chars): {data.get(\"text\", \"\")[:100]}...')"
    
    echo -e "\n"
}

# Función para benchmark de rendimiento
benchmark() {
    if [ -z "$1" ]; then
        echo "❌ Error: Proporciona la ruta del archivo"
        echo "Uso: benchmark /ruta/a/archivo.pdf"
        return 1
    fi
    
    echo "⏱️  Benchmark de rendimiento con: $1"
    
    for i in {1..3}; do
        echo "--- Intento $i ---"
        time curl -s -F "file=@$1" -F "lang=spa+eng" -F "optimize=1" "$SERVER_URL/ocr" > /dev/null
    done
    
    echo -e "\n"
}

# Función para mostrar ayuda
show_help() {
    echo "Funciones disponibles:"
    echo "  test_health                    - Probar endpoint de salud"
    echo "  test_image_ocr <imagen>        - Probar OCR con imagen"
    echo "  test_pdf_ocr <pdf>             - Probar OCR con PDF"
    echo "  test_languages <archivo>       - Probar diferentes idiomas"
    echo "  benchmark <archivo>            - Benchmark de rendimiento"
    echo ""
    echo "Ejemplos:"
    echo "  test_health"
    echo "  test_pdf_ocr ./documento.pdf"
    echo "  test_image_ocr ./imagen.jpg"
    echo "  test_languages ./documento.pdf"
    echo "  benchmark ./documento.pdf"
}

# Si se ejecuta el script directamente, mostrar ayuda
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    show_help
fi