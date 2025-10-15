# Mini‑server OCR Local — FastAPI + OCRmyPDF + Tesseract (PDF multipágina)

Solución **100% local y privada** para OCR de PDFs (multipágina) e imágenes, lista para desplegar en **Portainer/Docker** y consumir desde **n8n**.

---

## 📁 Estructura del proyecto

```
ocr-rest/
  ├─ Dockerfile
  ├─ app.py
  ├─ requirements.txt
  ├─ docker-compose.yml
  └─ README.md
```

---

## 🚀 Despliegue

### Con Docker Compose

```bash
# Construir y ejecutar
docker-compose up -d --build

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

### Con Portainer

1. Crear un nuevo Stack
2. Pegar el contenido de `docker-compose.yml`
3. Subir también `Dockerfile`, `app.py` y `requirements.txt` en el editor de archivos del stack
4. Hacer **Deploy**

---

## 🧪 Pruebas rápidas

```bash
# Salud del servicio
curl http://localhost:5050/health

# OCR de un PDF multipágina
curl -F "file=@/ruta/archivo.pdf" -F "lang=spa+eng" \
     -F "optimize=1" -F "deskew=1" -F "clean=1" \
     http://localhost:5050/ocr

# OCR de una imagen
curl -F "file=@/ruta/imagen.jpg" -F "lang=spa" http://localhost:5050/ocr
```

Respuesta típica:

```json
{
  "text": "Campeonato de Canarias Cadete, Junior y Sub21 ...",
  "pages": 3,
  "engine": "ocrmypdf+tesseract"
}
```

---

## 🔌 Uso con n8n

Configuración del nodo **HTTP Request**:

* **URL:** `http://TU_HOST:5050/ocr`
* **Method:** `POST`
* **Body Content Type:** `Form-Data`
* **Send Binary Data:** ✅
* **Binary Property:** `pdf`
* **Additional fields (form fields):**
  * `lang=spa+eng`
  * `optimize=1`
  * `deskew=1`
  * `clean=1`
* **Response Format:** `JSON`

---

## ⚙️ Parámetros disponibles

### `/ocr` endpoint

- **file** (required): Archivo PDF o imagen
- **lang** (default: "spa+eng"): Idiomas para OCR (formato Tesseract)
- **optimize** (default: 0): Nivel de optimización 0-3 para PDFs
- **deskew** (default: 1): Enderezar páginas (0/1)
- **clean** (default: 1): Limpiar artefactos de imagen (0/1)

### Formatos soportados

- **PDFs**: .pdf
- **Imágenes**: .png, .jpg, .jpeg, .tif, .tiff, .bmp

---

## 🛡️ Seguridad & buenas prácticas

* El servicio **no almacena** archivos: se usan directorios temporales que se borran por cada petición.
* Si expones el puerto fuera de tu LAN, pon **reverse proxy** (Traefik/Nginx) con **auth** y **HTTPS**.
* Ajusta CORS a los orígenes necesarios en `app.py`.
* Añade límites en tu proxy (máx. tamaño de subida) si esperas PDFs grandes.

---

## 🧰 Extensiones opcionales

### Más idiomas
Añade paquetes `tesseract-ocr-XXX` en el `Dockerfile`:
```dockerfile
tesseract-ocr-fra tesseract-ocr-deu tesseract-ocr-ita
```

### Salida por páginas
Modifica `app.py` para devolver un array `pages: [{n, text}]` leyendo el sidecar y dividiendo por saltos de página (`\f`).

### Cache
Si suben el mismo PDF, cachea por hash SHA-256 para mejorar rendimiento.

---

## 🐞 Troubleshooting

### Errores comunes

1. **"ocrmypdf error"**: Verificar que el PDF no esté corrupto
2. **"Solo PDF o imagen"**: Verificar extensión del archivo
3. **Memory issues**: Ajustar límites de memoria en docker-compose.yml

### Logs

```bash
# Ver logs del contenedor
docker logs ocr-rest

# Seguir logs en tiempo real
docker logs -f ocr-rest
```

---

## 📊 Recursos del sistema

- **CPU**: 0.5-2.0 cores (configurable)
- **RAM**: 512MB-2GB (configurable)
- **Almacenamiento**: Mínimo, solo para dependencias

---

## 🔧 Desarrollo local

Para desarrollo sin Docker:

```bash
# Instalar dependencias del sistema (Ubuntu/Debian)
sudo apt-get update && sudo apt-get install -y \
    tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng \
    ghostscript qpdf unpaper pngquant poppler-utils

# Instalar dependencias Python
pip install -r requirements.txt

# Ejecutar servidor
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Acceso en: http://localhost:8000