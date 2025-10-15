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
async def ocr(
    file: UploadFile = File(None),
    pdf: UploadFile = File(None),      # acepta 'pdf' o 'file'
    lang: str = Form("spa+eng"),
    optimize: int = Form(0),
    deskew: int = Form(1),
    clean: int = Form(1),
):
    up = file or pdf
    if up is None:
        raise HTTPException(400, detail="Falta campo file/pdf")

    # Detectar tipo por content-type o por magic bytes
    content_type = (up.content_type or "").lower()
    is_pdf_ct = content_type == "application/pdf"

    import tempfile, os, shutil
    with tempfile.TemporaryDirectory() as tmp:
        in_path = os.path.join(tmp, up.filename or "upload.bin")
        with open(in_path, "wb") as f:
            shutil.copyfileobj(up.file, f)

        # Leer cabecera para detectar PDF por magic bytes
        is_pdf_magic = False
        try:
            with open(in_path, "rb") as f:
                head = f.read(5)
                is_pdf_magic = head == b"%PDF-"
        except Exception:
            pass

        is_pdf = is_pdf_ct or is_pdf_magic or in_path.lower().endswith(".pdf")

        if not is_pdf:
            # Imagen → Tesseract directo
            try:
                import subprocess
                text = subprocess.check_output(["tesseract", in_path, "stdout", "-l", lang],
                                               stderr=subprocess.STDOUT).decode("utf-8", "ignore")
                return {"text": text, "pages": 1, "engine": "tesseract"}
            except subprocess.CalledProcessError as e:
                raise HTTPException(500, detail=e.output.decode("utf-8", "ignore"))

        # PDF → ocrmypdf + sidecar
        import subprocess
        out_pdf = os.path.join(tmp, "out.pdf")
        sidecar = os.path.join(tmp, "out.txt")
        cmd = ["ocrmypdf", "--force-ocr", "--language", lang, "--sidecar", sidecar]
        if optimize: cmd += ["--optimize", str(optimize)]
        if deskew:   cmd += ["--deskew"]
        if clean:    cmd += ["--clean"]
        cmd += [in_path, out_pdf]
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as e:
            raise HTTPException(500, detail=f"ocrmypdf error: {e}")

        text = ""
        if os.path.exists(sidecar):
            with open(sidecar, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        # obtener páginas (best-effort)
        pages = None
        try:
            info = subprocess.check_output(["pdfinfo", out_pdf]).decode("utf-8", "ignore")
            for line in info.splitlines():
                if line.lower().startswith("pages:"):
                    pages = int(line.split(":")[1].strip())
                    break
        except Exception:
            pass

        return {"text": text, "pages": pages, "engine": "ocrmypdf+tesseract"}
