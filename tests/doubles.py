"""Test-only stand-ins for Azure services. Never imported by the app."""
from __future__ import annotations

from app.analyzers import FIELD_SPECS
from app.models import Answer, Brief, Claim, DocType, Entity, Fact, Observation, Redaction, doc_id_for
from app.services.errors import ServiceError

DEFAULTS = {"cheque_number": "004718", "cheque_date": "2026-09-20", "amount_figures": "485000",
            "drawer_name": "Kalra Fabricators", "payee_name": "Sharma Steel Traders", "bank_name": "Northern Sample Bank",
            "presented_on": "2026-10-01", "return_date": "2026-10-03", "return_reason": "51 - FUNDS INSUFFICIENT",
            "notice_date": "2026-10-30", "demand_amount": "485000"}


class FakeExtractor:
    def extract(self, doc_type, content, content_type):
        did = doc_id_for(content)
        return [Fact(id=f"{did}-{s.key}", doc_id=did, key=s.key, label=s.label,
                     value=None if s.manual else DEFAULTS.get(s.key), manual=s.manual)
                for s in FIELD_SPECS[doc_type]]


class FakeTranscriber:
    def __init__(self, text="My cheque bounced. Call me on 98765 43210.", error=None):
        self.text, self.error = text, error

    def supported_locales(self):
        return ["en-IN", "hi-IN"]

    def transcribe(self, audio, content_type, locale):
        if self.error:
            raise self.error
        return self.text


class FakeSynth:
    def speak(self, text, locale):
        return b"MP3:" + text.encode()[:20]


class FakeAnalyzer:
    def redact_pii(self, text, language):
        return Redaction(redacted_text=text.replace("98765 43210", "[PHONENUMBER]"),
                         entities=[Entity(text="98765 43210", category="PhoneNumber")])

    def entities(self, text, language):
        return [Entity(text="cheque", category="Product")]

    def key_phrases(self, text, language):
        return ["cheque bounced"]


class FakeReasoner:
    def __init__(self, fail_inspect=False):
        self.fail_inspect = fail_inspect

    def draft_brief(self, facts, transcript_redacted):
        ids = [f.id for f in facts if f.key == "cheque_number"]
        return Brief(claims=[Claim(text="Cheque 004718 was drawn.", fact_ids=ids, section="instrument")],
                     flagged=[], model="test-deployment")

    def inspect_cheque_image(self, image, content_type):
        if self.fail_inspect:
            raise ServiceError("model", "The model is busy. Retry.", True)
        return [Observation(key="signature", label="Signature", status="present", note="")]


class FakeAssistant:
    def ask(self, question, matter_id):
        return Answer(text=f"echo: {question}")
