"""Azure Language: privacy redaction, entities and key phrases. The model only ever sees redacted text."""
from __future__ import annotations

from ..config import Settings
from ..models import Entity, Redaction
from .errors import ServiceError, from_exception
from .redact import apply_redactions


class AzureTextAnalyzer:
    service = "language"

    def __init__(self, settings: Settings, credential=None):
        from azure.ai.textanalytics import TextAnalyticsClient
        from azure.identity import DefaultAzureCredential
        self._c = TextAnalyticsClient(endpoint=settings.cognitive_base,
                                      credential=credential or DefaultAzureCredential())

    @staticmethod
    def _lang(language: str) -> str:
        return language.split("-")[0]

    def redact_pii(self, text: str, language: str) -> Redaction:
        try:
            res = self._c.recognize_pii_entities([text], language=self._lang(language))[0]
        except Exception as exc:  # noqa: BLE001
            raise from_exception(self.service, exc) from exc
        if res.is_error:
            raise ServiceError(self.service, "The privacy filter could not read this text. Nothing was sent to the model.")
        spans = [(e.offset, e.length, e.category) for e in res.entities]
        return Redaction(redacted_text=apply_redactions(text, spans),
                         entities=[Entity(text=e.text, category=e.category) for e in res.entities])

    def entities(self, text: str, language: str) -> list[Entity]:
        try:
            res = self._c.recognize_entities([text], language=self._lang(language))[0]
        except Exception as exc:  # noqa: BLE001
            raise from_exception(self.service, exc) from exc
        return [] if res.is_error else [Entity(text=e.text, category=e.category) for e in res.entities]

    def key_phrases(self, text: str, language: str) -> list[str]:
        try:
            res = self._c.extract_key_phrases([text], language=self._lang(language))[0]
        except Exception as exc:  # noqa: BLE001
            raise from_exception(self.service, exc) from exc
        return [] if res.is_error else list(res.key_phrases)
