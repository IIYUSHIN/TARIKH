"""The workflow, in order. Each step is a plain function call so it can be read, tested and explained."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable

from .models import Answer, Brief, DocType, Document, Transcript, doc_id_for
from .services.base import Assistant, Extractor, Reasoner, Synthesizer, TextAnalyzer, Transcriber
from .services.errors import ServiceError
from .store import Store

MAX_BYTES = 15 * 1024 * 1024
IMAGE_TYPES = {"image/png", "image/jpeg", "image/tiff", "image/bmp"}
EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/tiff": ".tif", "image/bmp": ".bmp", "application/pdf": ".pdf"}


class InputError(ValueError):
    """The request was fine as a request but the content cannot be used; the message says why."""


@dataclass
class Services:
    extractor: Extractor
    transcriber: Transcriber
    synthesizer: Synthesizer
    analyzer: TextAnalyzer
    reasoner: Reasoner
    assistant: Assistant


def sniff_type(content: bytes) -> str | None:
    """Trust the bytes, not the file name or the browser's guess."""
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if content[:5] == b"%PDF-":
        return "application/pdf"
    if content[:4] in (b"II*\x00", b"MM\x00*"):
        return "image/tiff"
    if content[:2] == b"BM":
        return "image/bmp"
    if content[4:12] in (b"ftypheic", b"ftypheix", b"ftyphevc", b"ftypmif1"):
        return "image/heic"
    return None


class Pipeline:
    def __init__(self, store: Store, services: Services, data_dir: Path | str, today: Callable[[], date] = date.today):
        self.store, self.s, self.data_dir, self.today = store, services, Path(data_dir), today

    # -- papers --------------------------------------------------------------
    def add_document(self, matter_id: str, doc_type: DocType, filename: str, content: bytes) -> tuple[Document, list[str]]:
        self.store.get_matter(matter_id)  # 404 early
        if not content:
            raise InputError("The file is empty.")
        if len(content) > MAX_BYTES:
            raise InputError(f"The file is {len(content) / 1048576:.0f} MB; the limit is {MAX_BYTES // 1048576} MB.")
        kind = sniff_type(content)
        if kind == "image/heic":
            raise InputError("HEIC photos are not supported. Share the photo as JPEG (iPhone: Settings, Camera, "
                             "Formats, Most Compatible) or upload a PDF.")
        if kind is None:
            raise InputError("That file is not a PNG, JPEG, PDF, TIFF or BMP image (it may be damaged or renamed).")
        facts = self.s.extractor.extract(doc_type, content, kind)
        warnings: list[str] = []
        observations = []
        if doc_type == DocType.CHEQUE and kind in IMAGE_TYPES:
            try:
                observations = self.s.reasoner.inspect_cheque_image(content, kind)
            except ServiceError as exc:   # the facts are already read; do not lose them
                warnings.append(f"Cheque inspection skipped: {exc.user_message}")
        doc_id = doc_id_for(content)
        folder = self.data_dir / "uploads" / matter_id
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{doc_id}{EXT[kind]}"
        path.write_bytes(content)
        doc = Document(id=doc_id, matter_id=matter_id, doc_type=doc_type, filename=filename or path.name,
                       path=str(path), facts=facts, observations=observations)
        self.store.save_document(matter_id, doc)
        return doc, warnings

    # -- client's account ----------------------------------------------------
    def add_voice(self, matter_id: str, audio: bytes, content_type: str, locale: str) -> Transcript:
        self.store.get_matter(matter_id)
        if not audio:
            raise InputError("The recording is empty.")
        text = self.s.transcriber.transcribe(audio, content_type, locale)
        lang = locale.split("-")[0]
        redaction = self.s.analyzer.redact_pii(text, lang)          # must succeed before anything goes to the model
        try:
            entities = self.s.analyzer.entities(text, lang)
            phrases = self.s.analyzer.key_phrases(redaction.redacted_text, lang)
        except ServiceError:
            entities, phrases = [], []                              # nice to have, never blocks the matter
        t = Transcript(language=locale, text=text, redacted_text=redaction.redacted_text,
                       entities=entities, key_phrases=phrases, redaction_route="source-language")
        self.store.save_transcript(matter_id, t)
        return t

    # -- brief ---------------------------------------------------------------
    def draft_brief(self, matter_id: str) -> Brief:
        m = self.store.get_matter(matter_id)
        cheque_facts = [f for d in m.documents if d.doc_type == DocType.CHEQUE for f in d.facts if f.value]
        if not cheque_facts:
            raise InputError("Add the cheque first. The brief needs at least one fact read from it.")
        facts = [f for d in m.documents for f in d.facts]
        brief = self.s.reasoner.draft_brief(facts, m.transcript.redacted_text if m.transcript else None)
        self.store.save_brief(matter_id, brief)
        return brief

    def approve(self, matter_id: str, actor: str) -> None:
        if not actor or not actor.strip():
            raise InputError("Enter the reviewing advocate's name to approve.")
        try:
            self.store.approve(matter_id, actor.strip())
        except ValueError as exc:
            raise InputError("Draft the brief before approving it.") from exc

    def speak_brief(self, matter_id: str, locale: str) -> bytes:
        m = self.store.get_matter(matter_id)
        if m.brief is None or m.approved_by is None:
            raise InputError("Approve the brief before it is read to a client.")
        return self.s.synthesizer.speak(" ".join(c.text for c in m.brief.claims), locale)

    def ask(self, matter_id: str, question: str) -> Answer:
        self.store.get_matter(matter_id)
        if not question or not question.strip():
            raise InputError("Type a question first.")
        return self.s.assistant.ask(question.strip(), matter_id)
