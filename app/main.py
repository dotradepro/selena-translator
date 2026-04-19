from __future__ import annotations

from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import argos_packages, helsinki, translator
from .models import (
    AvailablePackage,
    HelsinkiConvertRequest,
    InstallRequest,
    JobStatus,
    TranslateRequest,
    TranslateResponse,
)


WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(
    title="Selena Translator",
    description="Argos Translate + Helsinki-NLP model converter",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/languages")
def list_languages() -> dict:
    return {
        "languages": translator.installed_languages(),
        "pairs": translator.installed_pairs(),
    }


@app.get("/api/packages/available")
def list_available_packages() -> list[AvailablePackage]:
    return [AvailablePackage(**p) for p in argos_packages.available_packages()]


@app.post("/api/packages/install")
def install_package(req: InstallRequest) -> dict:
    try:
        return argos_packages.install_pair(req.source, req.target)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/packages/{source}-{target}")
def delete_package(source: str, target: str) -> dict:
    try:
        return argos_packages.uninstall_pair(source, target)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/translate", response_model=TranslateResponse)
def do_translate(req: TranslateRequest) -> TranslateResponse:
    try:
        out = translator.translate(req.text, req.source, req.target)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TranslateResponse(translation=out, source=req.source, target=req.target)


@app.get("/api/helsinki/catalog")
def helsinki_catalog() -> list[dict]:
    return helsinki.catalog()


@app.post("/api/helsinki/convert")
def helsinki_convert(req: HelsinkiConvertRequest, background: BackgroundTasks) -> dict:
    jid = helsinki.JOBS.create(req.model_id, req.direction)
    background.add_task(
        helsinki.run_conversion,
        jid,
        req.model_id,
        req.direction,
        req.language_token or "",
        req.quantization,
    )
    return {"job_id": jid}


@app.get("/api/helsinki/jobs/{jid}", response_model=JobStatus)
def helsinki_job(jid: str) -> JobStatus:
    job = helsinki.JOBS.get(jid)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return JobStatus(**job)


@app.get("/api/helsinki/download/{jid}")
def helsinki_download(jid: str):
    job = helsinki.JOBS.get(jid)
    if job is None or not job.get("archive_path"):
        raise HTTPException(status_code=404, detail="archive not ready")
    path = Path(job["archive_path"])
    if not path.is_file():
        raise HTTPException(status_code=410, detail="archive missing on disk")
    return FileResponse(
        path, media_type="application/gzip", filename=path.name
    )


@app.get("/")
def root():
    index = WEB_DIR / "index.html"
    if not index.is_file():
        return JSONResponse({"error": "web/index.html missing"}, status_code=500)
    return FileResponse(index, media_type="text/html")


if WEB_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="assets")
