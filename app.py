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
    # Validar tipo de archivo por extensión
    fname = (file.filename or "input").lower()
    allowed = (".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")
    if not any(fname.endswith(ext) for ext in allowed):
        raise HTTPException(400, detail="Solo PDF o imagen")

    with tempfile.TemporaryDirectory() as tmp:
        in_path = os.path.join(tmp, os.path.basename(fname))
        with open(in_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

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