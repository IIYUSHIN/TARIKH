"""What the pipeline needs from the outside world. Each Azure service implements one of these."""
from __future__ import annotations

from typing import Protocol

from ..models import Answer, Brief, DocType, Entity, Fact, Observation, Redaction


class Extractor(Protocol):
    def extract(self, doc_type: DocType, content: bytes, content_type: str) -> list[Fact]: ...


class Transcriber(Protocol):
    def supported_locales(self) -> list[str]: ...
    def transcribe(self, audio: bytes, content_type: str, locale: str) -> str: ...


class Synthesizer(Protocol):
    def speak(self, text: str, locale: str) -> bytes: ...


class TextAnalyzer(Protocol):
    def redact_pii(self, text: str, language: str) -> Redaction: ...
    def entities(self, text: str, language: str) -> list[Entity]: ...
    def key_phrases(self, text: str, language: str) -> list[str]: ...


class Reasoner(Protocol):
    def draft_brief(self, facts: list[Fact], transcript_redacted: str | None) -> Brief: ...
    def inspect_cheque_image(self, image: bytes, content_type: str) -> list[Observation]: ...


class Assistant(Protocol):
    def ask(self, question: str, matter_id: str) -> Answer: ...
