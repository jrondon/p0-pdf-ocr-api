from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import subprocess, tempfile, os, shutil

app = FastAPI(title="OCR Local", version="1.0")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ocr")
async def ocr_binary(
    request: Request,
):
    body = await request.body()
    if not body:
        raise HTTPException(400, "Cuerpo vacío")

    lang = request.headers.get("x-ocr-lang", "spa+eng")
    optimize = int(request.headers.get("x-ocr-optimize", "0"))
    deskew = request.headers.get("x-ocr-deskew", "1") == "1"
    clean = request.headers.get("x-ocr-clean", "1") == "1"

    with tempfile.TemporaryDirectory() as tmp:
        in_path = os.path.join(tmp, "upload.pdf")
        with open(in_path, "wb") as f:
            f.write(body)

        # Detectar PDF por magic bytes
        is_pdf = body[:5] == b"%PDF-"
        if not is_pdf:
            # tratar como imagen
            try:
                text = subprocess.check_output(
                    ["tesseract", in_path, "stdout", "-l", lang],
                    stderr=subprocess.STDOUT
                ).decode("utf-8", "ignore")
                return {"text": text, "pages": 1, "engine": "tesseract"}
            except subprocess.CalledProcessError as e:
                raise HTTPException(500, e.output.decode("utf-8", "ignore"))

        # PDF → ocrmypdf
        out_pdf = os.path.join(tmp, "out.pdf")
        sidecar = os.path.join(tmp, "out.txt")
        cmd = ["ocrmypdf", "--force-ocr", "--language", lang, "--sidecar", sidecar]
        if optimize: cmd += ["--optimize", str(optimize)]
        if deskew:   cmd += ["--deskew"]
        if clean:    cmd += ["--clean"]
        cmd += [in_path, out_pdf]
        subprocess.check_call(cmd)

        text = ""
        if os.path.exists(sidecar):
            with open(sidecar, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        return {"text": text, "engine": "ocrmypdf+tesseract"}