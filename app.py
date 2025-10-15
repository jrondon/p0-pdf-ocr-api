from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess, tempfile, os, shutil

app = FastAPI(title="OCR Local", version="1.0")

# CORS mínimo (ajusta orígenes si expones fuera de tu red)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ocr")
def ocr(
    file: UploadFile = File(...),
    lang: str = Form("spa+eng"),
    optimize: int = Form(0),           # 0..3 (ocrmypdf)
    deskew: int = Form(1),             # endereza páginas
    clean: int = Form(1),              # limpia artefactos
):
    # Leer el contenido del archivo
    file_content = file.file.read()
    file.file.seek(0)  # Reset para poder leerlo de nuevo si es necesario
    
    # Detectar tipo de archivo por magic bytes
    is_pdf = file_content[:5] == b"%PDF-"
    is_png = file_content[:8] == b"\x89PNG\r\n\x1a\n"
    is_jpg = file_content[:3] == b"\xff\xd8\xff"
    is_tiff = file_content[:4] in (b"II*\x00", b"MM\x00*")
    is_bmp = file_content[:2] == b"BM"
    
    # Validar que sea un tipo de archivo soportado
    if not (is_pdf or is_png or is_jpg or is_tiff or is_bmp):
        # Intentar validar también por extensión como fallback
        fname = (file.filename or "input").lower()
        allowed = (".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")
        if not any(fname.endswith(ext) for ext in allowed):
            raise HTTPException(400, detail="Solo PDF o imagen (formato no reconocido)")
    
    # Determinar extensión correcta basada en el contenido
    if is_pdf:
        ext = ".pdf"
    elif is_png:
        ext = ".png"
    elif is_jpg:
        ext = ".jpg"
    elif is_tiff:
        ext = ".tiff"
    elif is_bmp:
        ext = ".bmp"
    else:
        # Usar el nombre original si existe
        fname = (file.filename or "input").lower()
        ext = os.path.splitext(fname)[1] or ".pdf"

    with tempfile.TemporaryDirectory() as tmp:
        in_path = os.path.join(tmp, f"upload{ext}")
        with open(in_path, "wb") as f:
            f.write(file_content)

        # Si es imagen: usar tesseract directo a stdout
        if not in_path.endswith(".pdf"):
            try:
                cmd = ["tesseract", in_path, "stdout", "-l", lang]
                text = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8", errors="ignore")
                return JSONResponse({"text": text, "pages": 1, "engine": "tesseract"})
            except subprocess.CalledProcessError as e:
                raise HTTPException(500, detail=e.output.decode("utf-8", errors="ignore"))

        # PDF multipágina: usar ocrmypdf con sidecar de texto
        out_pdf = os.path.join(tmp, "out.pdf")
        sidecar = os.path.join(tmp, "out.txt")
        cmd = [
            "ocrmypdf", "--force-ocr",
            "--language", lang,
            "--sidecar", sidecar,
        ]
        if optimize:
            cmd += ["--optimize", str(optimize)]
        if deskew:
            cmd += ["--deskew"]
        if clean:
            cmd += ["--clean"]
        cmd += [in_path, out_pdf]

        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as e:
            raise HTTPException(500, detail=f"ocrmypdf error: {e}")

        text = ""
        if os.path.exists(sidecar):
            with open(sidecar, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        # Intento obtener número de páginas (poppler utils)
        pages = 0
        try:
            out = subprocess.check_output(["pdfinfo", out_pdf]).decode("utf-8", errors="ignore")
            for line in out.splitlines():
                if line.lower().startswith("pages:"):
                    pages = int(line.split(":")[1].strip())
                    break
        except Exception:
            pages = None

        return JSONResponse({"text": text, "pages": pages, "engine": "ocrmypdf+tesseract"})