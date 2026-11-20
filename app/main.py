"""HTTP layer: thin routes over the pipeline, plus the static front end."""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .analyzers import FIELD_SPECS
from .config import Settings
from .matter_dates import window_dict, windows_for_matter
from .models import DocType
from .pipeline import InputError, Pipeline, Services
from .services.base import Assistant, Extractor, Reasoner, Synthesizer, TextAnalyzer, Transcriber
from .services.errors import ServiceError
from .store import Store

STATIC = Path(__file__).parent / "static"
SAMPLES = Path(__file__).resolve().parent.parent / "samples"
VOICE_LOCALES = {"en-IN": "English", "hi-IN": "Hindi", "pa-IN": "Punjabi"}


class FactPatch(BaseModel):
    value: str | None = None
    actor: str = "Advocate"


class Approve(BaseModel):
    actor: str = ""


class Ask(BaseModel):
    question: str = ""


class Speak(BaseModel):
    locale: str = "en-IN"


class NewMatter(BaseModel):
    title: str = "Untitled matter"


def _date_keys() -> set[str]:
    return {s.key for specs in FIELD_SPECS.values() for s in specs if s.type == "date"}


def create_app(pipeline: Pipeline, store: Store, data_dir: Path | str, mode: str,
               recorded_at: Callable[[], str | None], deployment: str) -> FastAPI:
    app = FastAPI(title="Tarikh")
    date_keys = _date_keys()

    @app.exception_handler(InputError)
    async def _input(_: Request, exc: InputError):
        return JSONResponse({"error": str(exc)}, status_code=422)

    @app.exception_handler(ServiceError)
    async def _service(_: Request, exc: ServiceError):
        return JSONResponse({"error": exc.user_message, "retryable": exc.retryable, "service": exc.service},
                            status_code=502)

    @app.exception_handler(KeyError)
    async def _missing(_: Request, exc: KeyError):
        return JSONResponse({"error": f"Not found: {exc.args[0] if exc.args else ''}"}, status_code=404)

    def parse_today(raw: str | None) -> date:
        if raw is None:
            return pipeline.today()
        try:
            return date.fromisoformat(raw)
        except ValueError:
            raise InputError("today must be a date like 2026-11-21") from None

    @app.get("/api/mode")
    def get_mode():
        return {"mode": mode, "recorded_at": recorded_at(), "deployment": deployment, "today": pipeline.today().isoformat()}

    @app.get("/api/locales")
    def locales():
        supported = set(pipeline.s.transcriber.supported_locales())
        return [{"locale": k, "name": v, "available": k in supported} for k, v in VOICE_LOCALES.items()]

    @app.get("/api/matters")
    def list_matters():
        today = pipeline.today()
        out = []
        for m in store.list_matters():
            w = {x.key: x for x in windows_for_matter(m, today)}
            out.append({"id": m.id, "title": m.title, "created_at": m.created_at, "documents": len(m.documents),
                        "approved_by": m.approved_by, "complaint": window_dict(w["complaint"])})
        return out

    @app.post("/api/sample-matter")
    def sample_matter():
        """A demo matter from the fictional sample papers in /samples, so a first run needs no files of its own."""
        m = store.create_matter("Sharma Steel Traders v. Kalra Fabricators (fictional sample)")
        for doc_type, name in [(DocType.CHEQUE, "cheque.png"), (DocType.RETURN_MEMO, "return_memo.png"),
                               (DocType.DEMAND_NOTICE, "demand_notice.png")]:
            pipeline.add_document(m.id, doc_type, name, (SAMPLES / name).read_bytes())
        return store.get_matter(m.id)

    @app.post("/api/matters")
    def new_matter(body: NewMatter):
        return store.create_matter(body.title.strip() or "Untitled matter")

    @app.get("/api/matters/{matter_id}")
    def get_matter(matter_id: str, today: str | None = None):
        m, t = store.get_matter(matter_id), parse_today(today)
        return {"matter": m, "windows": [window_dict(w) for w in windows_for_matter(m, t)],
                "audit": store.audit(matter_id), "today": t.isoformat()}

    @app.get("/api/matters/{matter_id}/deadlines")
    def deadlines(matter_id: str, today: str | None = None):
        t = parse_today(today)
        return {"as_of": t.isoformat(), "windows": [window_dict(w) for w in windows_for_matter(store.get_matter(matter_id), t)]}

    @app.post("/api/matters/{matter_id}/documents")
    async def add_document(matter_id: str, doc_type: str = Form(...), file: UploadFile = File(...)):
        try:
            dt = DocType(doc_type)
        except ValueError:
            raise InputError("doc_type must be cheque, return_memo or demand_notice") from None
        doc, warnings = pipeline.add_document(matter_id, dt, file.filename or "", await file.read())
        return {"document": doc, "warnings": warnings}

    @app.get("/api/matters/{matter_id}/documents/{doc_id}/file")
    def document_file(matter_id: str, doc_id: str):
        for d in store.get_matter(matter_id).documents:
            if d.id == doc_id and Path(d.path).exists():
                return FileResponse(d.path)
        raise KeyError(doc_id)

    @app.patch("/api/facts/{fact_id}")
    def patch_fact(fact_id: str, body: FactPatch):
        fact = store.get_fact(fact_id)   # KeyError -> 404
        value = (body.value or "").strip() or None
        if value and fact.key in date_keys:
            try:
                date.fromisoformat(value)
            except ValueError:
                raise InputError("Enter dates as YYYY-MM-DD, for example 2026-09-20.") from None
        store.update_fact(fact_id, value, actor=body.actor.strip() or "Advocate")
        return store.get_fact(fact_id)

    @app.post("/api/matters/{matter_id}/voice")
    async def voice(matter_id: str, locale: str = Form("en-IN"), audio: UploadFile = File(...)):
        return pipeline.add_voice(matter_id, await audio.read(), audio.content_type or "audio/wav", locale)

    @app.post("/api/matters/{matter_id}/brief")
    def brief(matter_id: str):
        return pipeline.draft_brief(matter_id)

    @app.post("/api/matters/{matter_id}/approve")
    def approve(matter_id: str, body: Approve):
        pipeline.approve(matter_id, body.actor)
        return store.get_matter(matter_id)

    @app.post("/api/matters/{matter_id}/ask")
    def ask(matter_id: str, body: Ask):
        return pipeline.ask(matter_id, body.question)

    @app.post("/api/matters/{matter_id}/speak")
    def speak(matter_id: str, body: Speak):
        return Response(pipeline.speak_brief(matter_id, body.locale), media_type="audio/mpeg")

    if STATIC.exists():
        app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
    return app


def build_app() -> FastAPI:
    """Wire real Azure services (live) or recorded ones (replay) from environment settings."""
    from dotenv import load_dotenv
    from .services.recorder import Recorder
    load_dotenv()
    settings = Settings.from_env()
    store = Store(settings.data_dir / "tarikh.db")
    pairs = [("extraction", Extractor), ("speech-in", Transcriber), ("speech-out", Synthesizer),
             ("language", TextAnalyzer), ("model", Reasoner), ("agent", Assistant)]
    if settings.mode == "live":
        if not settings.project_endpoint or not settings.model_deployment:
            raise RuntimeError("Set AZURE_AI_PROJECT_ENDPOINT and AZURE_AI_MODEL_DEPLOYMENT_NAME in .env "
                               "(see docs/azure-setup.md), or run with TARIKH_MODE=replay.")
        from .services.agent import FoundryAssistant
        from .services.extraction import ContentUnderstandingExtractor
        from .services.language import AzureTextAnalyzer
        from .services.reasoning import FoundryReasoner
        from .services.speech import AzureSynthesizer, AzureTranscriber
        real = [ContentUnderstandingExtractor(settings), AzureTranscriber(settings), AzureSynthesizer(settings),
                AzureTextAnalyzer(settings), FoundryReasoner(settings), FoundryAssistant(settings, store)]
        record = os.environ.get("TARIKH_RECORD", "1") != "0"
        wrapped = [Recorder(r, proto, name, settings.cassette_dir, "live") if record else r
                   for r, (name, proto) in zip(real, pairs)]
    else:
        wrapped = [Recorder(None, proto, name, settings.cassette_dir, "replay") for name, proto in pairs]
    recorders = [w for w in wrapped if isinstance(w, Recorder)]
    def recorded_at():
        stamps = [s for s in (r.recorded_at() for r in recorders) if s]
        return max(stamps) if stamps else None
    pipe = Pipeline(store, Services(*wrapped), settings.data_dir)
    return create_app(pipe, store, settings.data_dir, settings.mode, recorded_at, settings.model_deployment)
