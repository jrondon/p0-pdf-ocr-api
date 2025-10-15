from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import subprocess, tempfile, os, shutil

app = FastAPI(title="OCR Local", version="1.0")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ocr")
async def ocr(
    file: UploadFile = File(None),          # n8n suele enviar campo 'file'
    pdf: UploadFile = File(None),           # por si envías 'pdf'
    lang: str = Form("spa+eng"),
    optimize: int = Form(0),
    deskew: int = Form(1),
    clean: int = Form(1),
):
    up = file or pdf
    if up is None:
        raise HTTPException(400, detail="Falta campo file/pdf")

    # Guardar a disco temporal
    with tempfile.TemporaryDirectory() as tmp:
        in_name = (up.filename or "upload.bin")
        in_path = os.path.join(tmp, in_name)
        with open(in_path, "wb") as f:
            shutil.copyfileobj(up.file, f)

        # Detectar si es PDF por content-type y/o magic bytes
        content_type = (up.content_type or "").lower()
        is_pdf_ct = (content_type == "application/pdf")
        is_pdf_magic = False
        try:
            with open(in_path, "rb") as f:
                is_pdf_magic = f.read(5) == b"%PDF-"
        except Exception:
            pass
        is_pdf = is_pdf_ct or is_pdf_magic or in_path.lower().endswith(".pdf")

        if not is_pdf:
            # Imagen → tesseract directo
            try:
                text = subprocess.check_output(
                    ["tesseract", in_path, "stdout", "-l", lang],
                    stderr=subprocess.STDOUT
                ).decode("utf-8", "ignore")
                return JSONResponse({"text": text, "pages": 1, "engine": "tesseract"})
            except subprocess.CalledProcessError as e:
                raise HTTPException(500, detail=e.output.decode("utf-8", "ignore"))

        # PDF → ocrmypdf con sidecar de texto
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

        # páginas (best-effort)
        pages = None
        try:
            info = subprocess.check_output(["pdfinfo", out_pdf]).decode("utf-8", "ignore")
            for line in info.splitlines():
                if line.lower().startswith("pages:"):
                    pages = int(line.split(":")[1].strip()); break
        except Exception:
            pass

        return JSONResponse({"text": text, "pages": pages, "engine": "ocrmypdf+tesseract"})
