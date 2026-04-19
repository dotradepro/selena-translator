from __future__ import annotations

import threading
from typing import Optional

import argostranslate.package
import argostranslate.translate


_lock = threading.Lock()
_loaded = False


def _ensure_loaded() -> None:
    global _loaded
    with _lock:
        if _loaded:
            return
        argostranslate.package.update_package_index()
        _loaded = True


def translate(text: str, source: str, target: str) -> str:
    _ensure_loaded()
    installed = argostranslate.translate.get_installed_languages()
    src = next((l for l in installed if l.code == source), None)
    tgt = next((l for l in installed if l.code == target), None)
    if src is None:
        raise ValueError(f"source language not installed: {source}")
    if tgt is None:
        raise ValueError(f"target language not installed: {target}")
    translation = src.get_translation(tgt)
    if translation is None:
        raise ValueError(f"no translation pair installed: {source}->{target}")
    return translation.translate(text)


def installed_pairs() -> list[dict]:
    _ensure_loaded()
    pairs: list[dict] = []
    for src in argostranslate.translate.get_installed_languages():
        for tgt in argostranslate.translate.get_installed_languages():
            if src.code == tgt.code:
                continue
            if src.get_translation(tgt) is not None:
                pairs.append(
                    {
                        "code": f"{src.code}-{tgt.code}",
                        "from_code": src.code,
                        "from_name": src.name,
                        "to_code": tgt.code,
                        "to_name": tgt.name,
                    }
                )
    return pairs


def installed_languages() -> list[dict]:
    _ensure_loaded()
    return [
        {"code": lang.code, "name": lang.name}
        for lang in argostranslate.translate.get_installed_languages()
    ]
