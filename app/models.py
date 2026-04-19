from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)
    source: str = Field(..., min_length=2, max_length=8, alias="from")
    target: str = Field(..., min_length=2, max_length=8, alias="to")

    model_config = {"populate_by_name": True}


class TranslateResponse(BaseModel):
    translation: str
    source: str
    target: str


class LanguagePair(BaseModel):
    code: str
    from_code: str
    from_name: str
    to_code: str
    to_name: str


class AvailablePackage(BaseModel):
    from_code: str
    from_name: str
    to_code: str
    to_name: str
    package_version: Optional[str] = None
    installed: bool = False


class InstallRequest(BaseModel):
    source: str = Field(..., alias="from")
    target: str = Field(..., alias="to")

    model_config = {"populate_by_name": True}


class HelsinkiConvertRequest(BaseModel):
    model_id: str = Field(..., description="HuggingFace repo ID e.g. Helsinki-NLP/opus-mt-tc-big-en-zle")
    direction: str = Field(..., description="Archive direction code e.g. en-uk")
    language_token: Optional[str] = Field(None, description="Optional multi-target token e.g. >>ukr<<")
    quantization: str = Field("int8", description="int8 | int16 | float16 | float32")


class JobStatus(BaseModel):
    id: str
    state: str
    progress: int
    log: list[str]
    archive_path: Optional[str] = None
    error: Optional[str] = None
    model_id: Optional[str] = None
    direction: Optional[str] = None
