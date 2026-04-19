from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


DATA_DIR = Path(os.environ.get("HELSINKI_OUT_DIR", "/app/data/helsinki-out"))
HF_CACHE = Path(os.environ.get("HF_HOME", str(Path.home() / ".cache" / "huggingface")))

DATA_DIR.mkdir(parents=True, exist_ok=True)


CATALOG: list[dict] = [
    {
        "direction": "uk-en",
        "model_id": "Helsinki-NLP/opus-mt-tc-big-zle-en",
        "language_token": "",
        "description": "East Slavic → English (multi-source: uk/ru/be)",
    },
    {
        "direction": "en-uk",
        "model_id": "Helsinki-NLP/opus-mt-tc-big-en-zle",
        "language_token": ">>ukr<<",
        "description": "English → East Slavic (requires >>ukr<<, >>rus<<, or >>bel<<)",
    },
    {
        "direction": "en-ru",
        "model_id": "Helsinki-NLP/opus-mt-tc-big-en-zle",
        "language_token": ">>rus<<",
        "description": "English → Russian (same multi-target model as en-uk)",
    },
    {
        "direction": "de-en",
        "model_id": "Helsinki-NLP/opus-mt-tc-big-gem-en",
        "language_token": "",
        "description": "Germanic → English",
    },
    {
        "direction": "en-de",
        "model_id": "Helsinki-NLP/opus-mt-tc-big-en-gem",
        "language_token": ">>deu<<",
        "description": "English → Germanic",
    },
    {
        "direction": "fr-en",
        "model_id": "Helsinki-NLP/opus-mt-tc-big-rom-en",
        "language_token": "",
        "description": "Romance → English",
    },
    {
        "direction": "en-fr",
        "model_id": "Helsinki-NLP/opus-mt-tc-big-en-rom",
        "language_token": ">>fra<<",
        "description": "English → Romance",
    },
    {
        "direction": "en-es",
        "model_id": "Helsinki-NLP/opus-mt-tc-big-en-rom",
        "language_token": ">>spa<<",
        "description": "English → Spanish (via Romance multi-target)",
    },
    {
        "direction": "es-en",
        "model_id": "Helsinki-NLP/opus-mt-tc-big-rom-en",
        "language_token": "",
        "description": "Spanish → English",
    },
    {
        "direction": "en-it",
        "model_id": "Helsinki-NLP/opus-mt-tc-big-en-rom",
        "language_token": ">>ita<<",
        "description": "English → Italian",
    },
    {
        "direction": "en-pt",
        "model_id": "Helsinki-NLP/opus-mt-tc-big-en-rom",
        "language_token": ">>por<<",
        "description": "English → Portuguese",
    },
    {
        "direction": "en-pl",
        "model_id": "Helsinki-NLP/opus-mt-en-sla",
        "language_token": ">>pol<<",
        "description": "English → Polish (via Slavic multi-target)",
    },
    {
        "direction": "en-tr",
        "model_id": "Helsinki-NLP/opus-mt-en-trk",
        "language_token": ">>tur<<",
        "description": "English → Turkish",
    },
    {
        "direction": "en-nl",
        "model_id": "Helsinki-NLP/opus-mt-tc-big-en-gem",
        "language_token": ">>nld<<",
        "description": "English → Dutch",
    },
]


def catalog() -> list[dict]:
    return CATALOG


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, dict] = {}
        self._lock = threading.Lock()

    def create(self, model_id: str, direction: str) -> str:
        jid = uuid.uuid4().hex[:12]
        with self._lock:
            self._jobs[jid] = {
                "id": jid,
                "state": "queued",
                "progress": 0,
                "log": [],
                "archive_path": None,
                "error": None,
                "model_id": model_id,
                "direction": direction,
            }
        return jid

    def update(self, jid: str, **fields) -> None:
        with self._lock:
            job = self._jobs.get(jid)
            if not job:
                return
            if "log_append" in fields:
                job["log"].append(fields.pop("log_append"))
            job.update(fields)

    def get(self, jid: str) -> Optional[dict]:
        with self._lock:
            job = self._jobs.get(jid)
            return dict(job) if job else None


JOBS = JobStore()


def _log(jid: str, message: str) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    JOBS.update(jid, log_append=f"[{timestamp}] {message}")


def _find_spm_files(snapshot_dir: Path) -> tuple[Path, Path]:
    source = snapshot_dir / "source.spm"
    target = snapshot_dir / "target.spm"
    if source.is_file() and target.is_file():
        return source, target
    # Fallback: scan for *.spm
    spms = sorted(snapshot_dir.rglob("*.spm"))
    if len(spms) >= 2:
        s = next((p for p in spms if "source" in p.name), spms[0])
        t = next((p for p in spms if "target" in p.name), spms[-1])
        return s, t
    raise FileNotFoundError(f"SentencePiece files not found under {snapshot_dir}")


def run_conversion(
    jid: str, model_id: str, direction: str, language_token: str, quantization: str
) -> None:
    try:
        JOBS.update(jid, state="running", progress=5)
        _log(jid, f"Starting conversion for {model_id} ({direction})")

        from huggingface_hub import snapshot_download

        _log(jid, "Downloading model snapshot from HuggingFace")
        snapshot = Path(
            snapshot_download(
                repo_id=model_id,
                cache_dir=str(HF_CACHE / "hub"),
                allow_patterns=[
                    "*.json",
                    "*.spm",
                    "*.bin",
                    "*.safetensors",
                    "tokenizer*",
                    "vocab*",
                ],
            )
        )
        _log(jid, f"Snapshot at {snapshot}")
        JOBS.update(jid, progress=40)

        work = DATA_DIR / jid
        work.mkdir(parents=True, exist_ok=True)
        ct2_out = work / "ct2"
        if ct2_out.exists():
            shutil.rmtree(ct2_out)

        _log(jid, f"Running ct2-transformers-converter (--quantization {quantization})")
        result = subprocess.run(
            [
                "ct2-transformers-converter",
                "--model",
                str(snapshot),
                "--quantization",
                quantization,
                "--output_dir",
                str(ct2_out),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"ct2-transformers-converter failed: {result.stderr.strip() or result.stdout.strip()}"
            )
        _log(jid, "CTranslate2 conversion complete")
        JOBS.update(jid, progress=75)

        src_spm, tgt_spm = _find_spm_files(snapshot)
        shutil.copyfile(src_spm, ct2_out / "source.spm")
        shutil.copyfile(tgt_spm, ct2_out / "target.spm")
        _log(jid, "Copied SentencePiece tokenizers")

        metadata = {
            "model_id": model_id,
            "direction": direction,
            "language_token": language_token or "",
            "converted_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "quantization": quantization,
            "tool": "selena-translator",
        }
        (ct2_out / "metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )
        _log(jid, "Wrote metadata.json")
        JOBS.update(jid, progress=90)

        archive = work / f"{direction}.tar.gz"
        _log(jid, f"Packaging archive {archive.name}")
        subprocess.run(
            ["tar", "-czf", str(archive), "-C", str(ct2_out), "."],
            check=True,
        )
        size_mb = archive.stat().st_size / (1024 * 1024)
        _log(jid, f"Archive ready: {archive.name} ({size_mb:.1f} MB)")

        JOBS.update(
            jid,
            state="done",
            progress=100,
            archive_path=str(archive),
        )
    except Exception as exc:  # noqa: BLE001
        JOBS.update(jid, state="error", error=str(exc))
        _log(jid, f"ERROR: {exc}")
