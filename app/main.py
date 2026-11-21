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

from .accounts import AccountError, Accounts
from .analyzers import FIELD_SPECS
from .config import Settings
from .desk import STAGES, parse_return_file, sample_profiles, view
from .matter_dates import window_dict, windows_for_matter
from .models import DocType
from .pipeline import InputError, Pipeline, Services
from .services.base import Assistant, Extractor, Reasoner, Synthesizer, TextAnalyzer, Transcriber
from .services.errors import ServiceError
from .store import Store

STATIC = Path(__file__).parent / "static"
SITE = Path(__file__).resolve().parent.parent / "site" / "dist"
COOKIE = "tarikh_session"
OPEN_API = {"/api/mode", "/api/auth/signup", "/api/auth/signin", "/api/auth/signout", "/api/me"}
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
    complainant: str = ""
    accused: str = ""
    amount: str = ""
    chequeNo: str = ""
    court: str = ""
    entries: dict[str, str] = {}


class SignUp(BaseModel):
    name: str = ""
    email: str = ""
    password: str = ""
    chambers: str = ""
    kind: str = "advocate"


class SignIn(BaseModel):
    email: str = ""
    password: str = ""


class ProfilePatch(BaseModel):
    complainant: str | None = None
    accused: str | None = None
    amount: str | None = None
    chequeNo: str | None = None
    court: str | None = None
    caseNo: str | None = None
    filed: str | None = None
    stage: str | None = None
    email: str | None = None
    phone: str | None = None
    advocate: str | None = None
    entries: dict[str, str | None] | None = None


class Hearing(BaseModel):
    date: str
    purpose: str
    outcome: str = ""
    next_date: str | None = None
    next_purpose: str = ""


class Settlement(BaseModel):
    total: int
    parts: int = 1
    paid: int = 0


class DraftApproval(BaseModel):
    title: str
    actor: str = ""


class ImportFile(BaseModel):
    csv: str = ""
    complainant: str = ""
    sample: bool = False


class Assign(BaseModel):
    ids: list[str]
    advocate: str


def _date_keys() -> set[str]:
    return {s.key for specs in FIELD_SPECS.values() for s in specs if s.type == "date"}


def create_app(pipeline: Pipeline, store: Store, data_dir: Path | str, mode: str,
               recorded_at: Callable[[], str | None], deployment: str,
               accounts: Accounts | None = None, site_dir: Path | None = None) -> FastAPI:
    """With accounts, every /api route except sign-in needs a session and sees only its owner's matters.
    Without accounts (the unit tests), it is a single-user app."""
    app = FastAPI(title="Tarikh")
    date_keys = _date_keys()

    @app.middleware("http")
    async def _session(request: Request, call_next):
        request.state.user = accounts.user_for(request.cookies.get(COOKIE)) if accounts else None
        path = request.url.path
        if accounts and path.startswith("/api/") and path not in OPEN_API and request.state.user is None:
            return JSONResponse({"error": "Sign in to continue."}, status_code=401)
        return await call_next(request)

    def uid(request: Request) -> str:
        return request.state.user.id if request.state.user else ""

    def actor(request: Request, fallback: str = "Advocate") -> str:
        return request.state.user.name if request.state.user else fallback

    def own(request: Request, matter_id: str):
        m = store.get_matter(matter_id)
        if accounts and m.owner != uid(request):
            raise KeyError(matter_id)          # another person's matter does not exist for you
        return m

    @app.exception_handler(AccountError)
    async def _account(_: Request, exc: AccountError):
        return JSONResponse({"error": str(exc)}, status_code=422)

    def _signed_in(user) -> JSONResponse:
        resp = JSONResponse({"user": user.__dict__})
        resp.set_cookie(COOKIE, accounts.new_session(user), httponly=True, samesite="lax", max_age=14 * 86400)
        return resp

    @app.post("/api/auth/signup")
    def signup(body: SignUp):
        if not accounts:
            raise InputError("Accounts are not enabled.")
        return _signed_in(accounts.sign_up(body.email, body.name, body.password, body.chambers, body.kind))

    @app.post("/api/auth/signin")
    def signin(body: SignIn):
        if not accounts:
            raise InputError("Accounts are not enabled.")
        return _signed_in(accounts.sign_in(body.email, body.password))

    @app.post("/api/auth/signout")
    def signout(request: Request):
        if accounts:
            accounts.end_session(request.cookies.get(COOKIE))
        resp = JSONResponse({"ok": True})
        resp.delete_cookie(COOKIE)
        return resp

    @app.get("/api/me")
    def me(request: Request):
        u = request.state.user
        return {"user": u.__dict__ if u else None, "mode": mode, "today": pipeline.today().isoformat()}

    @app.get("/api/desk")
    def desk(request: Request):
        t = pipeline.today()
        return {"today": t.isoformat(), "matters": [view(m, t) for m in store.list_matters(uid(request) if accounts else None)]}

    @app.post("/api/desk/samples")
    def load_samples(request: Request):
        existing = {m.profile.get("ref") for m in store.list_matters(uid(request) if accounts else None)}
        made = 0
        for title, prof in sample_profiles():
            if prof["ref"] in existing:
                continue
            m = store.create_matter(title, owner=uid(request), profile=prof)
            store.log(m.id, actor(request), "sample_loaded", {"ref": prof["ref"]})
            if prof["ref"] == "KF-1042":
                for doc_type, name in [(DocType.CHEQUE, "cheque.png"), (DocType.RETURN_MEMO, "return_memo.png"),
                                       (DocType.DEMAND_NOTICE, "demand_notice.png")]:
                    try:
                        pipeline.add_document(m.id, doc_type, name, (SAMPLES / name).read_bytes())
                    except ServiceError:
                        pass                # papers are optional for samples; the entered dates still count
            made += 1
        return {"created": made}

    @app.post("/api/desk/import")
    def import_file(request: Request, body: ImportFile):
        text = (SAMPLES / "return_file.csv").read_text(encoding="utf-8") if body.sample else body.csv
        rows, problems = parse_return_file(text, body.complainant.strip() or (request.state.user.chambers if request.state.user else "Complainant"))
        for title, prof in rows:
            m = store.create_matter(title, owner=uid(request), profile=prof)
            store.log(m.id, actor(request), "imported", {"ref": prof.get("ref")})
        return {"created": len(rows), "problems": problems}

    @app.post("/api/desk/assign")
    def assign(request: Request, body: Assign):
        for mid in body.ids:
            own(request, mid)
            store.update_profile(mid, {"advocate": body.advocate.strip()}, actor(request), "assigned")
        return {"assigned": len(body.ids)}

    @app.get("/api/desk/{matter_id}")
    def desk_matter(request: Request, matter_id: str):
        m = own(request, matter_id)
        return view(m, pipeline.today(), store.audit(matter_id))

    @app.patch("/api/desk/{matter_id}")
    def patch_matter(request: Request, matter_id: str, body: ProfilePatch):
        own(request, matter_id)
        changes = body.model_dump(exclude_none=True)
        if changes.get("stage") and changes["stage"] not in STAGES:
            raise InputError("Unknown stage.")
        for k, v in (changes.get("entries") or {}).items():
            if v:
                try:
                    date.fromisoformat(v)
                except ValueError:
                    raise InputError("Enter dates as YYYY-MM-DD, for example 2026-11-21.") from None
        for k in ("filed",):
            if changes.get(k):
                date.fromisoformat(changes[k])
        m = store.update_profile(matter_id, changes, actor(request))
        return view(m, pipeline.today(), store.audit(matter_id))

    @app.post("/api/desk/{matter_id}/hearings")
    def add_hearing(request: Request, matter_id: str, body: Hearing):
        m = own(request, matter_id)
        try:
            date.fromisoformat(body.date)
            if body.next_date:
                date.fromisoformat(body.next_date)
        except ValueError:
            raise InputError("Enter dates as YYYY-MM-DD.") from None
        if not body.purpose.strip():
            raise InputError("Say what the hearing was for.")
        hs = (m.profile.get("hearings") or []) + [[body.date, body.purpose.strip(), body.outcome.strip() or "Recorded"]]
        hs.sort(key=lambda h: h[0])
        nxt = [body.next_date, body.next_purpose.strip() or "Next hearing"] if body.next_date else None
        m = store.update_profile(matter_id, {"hearings": hs, "next": nxt}, actor(request), "hearing_recorded")
        return view(m, pipeline.today(), store.audit(matter_id))

    @app.post("/api/desk/{matter_id}/settlement")
    def set_settlement(request: Request, matter_id: str, body: Settlement):
        own(request, matter_id)
        if body.total <= 0 or body.parts < 1 or not (0 <= body.paid <= body.parts):
            raise InputError("Check the amount, the number of instalments and how many are paid.")
        m = store.update_profile(matter_id, {"settlement": body.model_dump()}, actor(request), "settlement_recorded")
        return view(m, pipeline.today(), store.audit(matter_id))

    @app.post("/api/desk/{matter_id}/drafts/approve")
    def approve_draft(request: Request, matter_id: str, body: DraftApproval):
        m = own(request, matter_id)
        who = body.actor.strip() or actor(request, "")
        if not who:
            raise InputError("Type your name to approve.")
        drafts = [d for d in (m.profile.get("drafts") or []) if d.get("t") != body.title]
        drafts.append({"t": body.title, "s": "Approved", "by": who})
        m = store.update_profile(matter_id, {"drafts": drafts}, who, "draft_approved")
        return view(m, pipeline.today(), store.audit(matter_id))

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
    def list_matters(request: Request):
        today = pipeline.today()
        out = []
        for m in store.list_matters(uid(request) if accounts else None):
            w = {x.key: x for x in windows_for_matter(m, today)}
            out.append({"id": m.id, "title": m.title, "created_at": m.created_at, "documents": len(m.documents),
                        "approved_by": m.approved_by, "complaint": window_dict(w["complaint"])})
        return out

    @app.post("/api/sample-matter")
    def sample_matter(request: Request):
        """A matter from the fictional sample papers in /samples, so a first run needs no files of its own."""
        m = store.create_matter("Sharma Steel Traders v. Kalra Fabricators (fictional sample)", owner=uid(request))
        for doc_type, name in [(DocType.CHEQUE, "cheque.png"), (DocType.RETURN_MEMO, "return_memo.png"),
                               (DocType.DEMAND_NOTICE, "demand_notice.png")]:
            pipeline.add_document(m.id, doc_type, name, (SAMPLES / name).read_bytes())
        return store.get_matter(m.id)

    @app.post("/api/matters")
    def new_matter(request: Request, body: NewMatter):
        for v in body.entries.values():
            if v:
                try:
                    date.fromisoformat(v)
                except ValueError:
                    raise InputError("Enter dates as YYYY-MM-DD, for example 2026-11-21.") from None
        title = body.title.strip()
        if body.complainant.strip() and body.accused.strip():
            title = f"{body.complainant.strip()} v. {body.accused.strip()}"
        prof = {k: v.strip() for k, v in {"complainant": body.complainant, "accused": body.accused, "amount": body.amount,
                                          "chequeNo": body.chequeNo, "court": body.court}.items() if v.strip()}
        prof["entries"] = {k: v for k, v in body.entries.items() if v}
        m = store.create_matter(title or "Untitled matter", owner=uid(request), profile=prof)
        store.log(m.id, actor(request), "matter_opened", {})
        return m

    @app.get("/api/matters/{matter_id}")
    def get_matter(request: Request, matter_id: str, today: str | None = None):
        m, t = own(request, matter_id), parse_today(today)
        return {"matter": m, "windows": [window_dict(w) for w in windows_for_matter(m, t)],
                "audit": store.audit(matter_id), "today": t.isoformat()}

    @app.get("/api/matters/{matter_id}/deadlines")
    def deadlines(request: Request, matter_id: str, today: str | None = None):
        t = parse_today(today)
        return {"as_of": t.isoformat(), "windows": [window_dict(w) for w in windows_for_matter(own(request, matter_id), t)]}

    @app.post("/api/matters/{matter_id}/documents")
    async def add_document(request: Request, matter_id: str, doc_type: str = Form(...), file: UploadFile = File(...)):
        own(request, matter_id)
        try:
            dt = DocType(doc_type)
        except ValueError:
            raise InputError("doc_type must be cheque, return_memo or demand_notice") from None
        doc, warnings = pipeline.add_document(matter_id, dt, file.filename or "", await file.read())
        return {"document": doc, "warnings": warnings}

    @app.get("/api/matters/{matter_id}/documents/{doc_id}/file")
    def document_file(request: Request, matter_id: str, doc_id: str):
        for d in own(request, matter_id).documents:
            if d.id == doc_id and Path(d.path).exists():
                return FileResponse(d.path)
        raise KeyError(doc_id)

    @app.patch("/api/facts/{fact_id}")
    def patch_fact(request: Request, fact_id: str, body: FactPatch):
        own(request, store.matter_id_for_fact(fact_id))
        fact = store.get_fact(fact_id)   # KeyError -> 404
        value = (body.value or "").strip() or None
        if value and fact.key in date_keys:
            try:
                date.fromisoformat(value)
            except ValueError:
                raise InputError("Enter dates as YYYY-MM-DD, for example 2026-09-20.") from None
        store.update_fact(fact_id, value, actor=actor(request, body.actor.strip() or "Advocate"))
        return store.get_fact(fact_id)

    @app.post("/api/matters/{matter_id}/voice")
    async def voice(request: Request, matter_id: str, locale: str = Form("en-IN"), audio: UploadFile = File(...)):
        own(request, matter_id)
        return pipeline.add_voice(matter_id, await audio.read(), audio.content_type or "audio/wav", locale)

    @app.post("/api/matters/{matter_id}/brief")
    def brief(request: Request, matter_id: str):
        own(request, matter_id)
        return pipeline.draft_brief(matter_id)

    @app.post("/api/matters/{matter_id}/approve")
    def approve(request: Request, matter_id: str, body: Approve):
        own(request, matter_id)
        pipeline.approve(matter_id, body.actor)
        return store.get_matter(matter_id)

    @app.post("/api/matters/{matter_id}/ask")
    def ask(request: Request, matter_id: str, body: Ask):
        own(request, matter_id)
        return pipeline.ask(matter_id, body.question)

    @app.post("/api/matters/{matter_id}/speak")
    def speak(request: Request, matter_id: str, body: Speak):
        own(request, matter_id)
        return Response(pipeline.speak_brief(matter_id, body.locale), media_type="audio/mpeg")

    if STATIC.exists():
        app.mount("/classic", StaticFiles(directory=STATIC, html=True), name="classic")
    site = site_dir or (SITE if SITE.exists() else None)
    if site and Path(site).exists():
        app.mount("/", StaticFiles(directory=site, html=True), name="site")
    elif STATIC.exists():
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
        from .services.extraction import ContentUnderstandingExtractor, ModelExtractor
        from .services.language import AzureTextAnalyzer
        from .services.reasoning import FoundryReasoner
        from .services.speech import AzureSynthesizer, AzureTranscriber
        reader = ModelExtractor(settings) if settings.extractor == "model" else ContentUnderstandingExtractor(settings)
        real = [reader, AzureTranscriber(settings), AzureSynthesizer(settings),
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
    return create_app(pipe, store, settings.data_dir, settings.mode, recorded_at, settings.model_deployment,
                      accounts=Accounts(settings.data_dir / "tarikh.db"))
