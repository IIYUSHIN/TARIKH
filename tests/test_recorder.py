import pytest
from azure.core.exceptions import HttpResponseError

from app.models import Answer, DocType, Fact
from app.services import errors
from app.services.base import Assistant, Extractor, Synthesizer
from app.services.errors import ServiceError
from app.services.recorder import Recorder


class FakeExtractor:
    def __init__(self):
        self.calls = 0

    def extract(self, doc_type, content, content_type):
        self.calls += 1
        return [Fact(id="d1-cheque_number", doc_id="d1", key="cheque_number", label="Cheque no.", value="004718")]


def _record(tmp_path):
    inner = FakeExtractor()
    rec = Recorder(inner, Extractor, "extraction", tmp_path, "live")
    return inner, rec.extract(DocType.CHEQUE, b"scan-bytes", "image/png")


def test_replay_returns_recorded_value_without_calling_inner(tmp_path):
    inner, recorded = _record(tmp_path)
    replay = Recorder(None, Extractor, "extraction", tmp_path, "replay")
    assert replay.extract(DocType.CHEQUE, b"scan-bytes", "image/png") == recorded
    assert inner.calls == 1


def test_replay_of_unrecorded_input_raises_service_error_that_says_so(tmp_path):
    _record(tmp_path)
    replay = Recorder(None, Extractor, "extraction", tmp_path, "replay")
    with pytest.raises(ServiceError, match="recorded") as e:
        replay.extract(DocType.CHEQUE, b"a different scan", "image/png")
    assert e.value.retryable is False


def test_bytes_results_survive_replay(tmp_path):
    class Voice:
        def speak(self, text, locale):
            return b"\x00\x01RIFF"
    Recorder(Voice(), Synthesizer, "speech", tmp_path, "live").speak("hello", "en-IN")
    assert Recorder(None, Synthesizer, "speech", tmp_path, "replay").speak("hello", "en-IN") == b"\x00\x01RIFF"


def test_matter_id_does_not_affect_replay_key(tmp_path):
    class Bot:
        def ask(self, question, matter_id):
            return Answer(text=f"answer for {matter_id}")
    Recorder(Bot(), Assistant, "agent", tmp_path, "live").ask("When must I file?", "m_one")
    got = Recorder(None, Assistant, "agent", tmp_path, "replay").ask("When must I file?", "m_two")
    assert got.text == "answer for m_one"


def test_429_maps_to_retryable_service_error():
    exc = HttpResponseError("too many requests")
    exc.status_code = 429
    err = errors.from_exception("extraction", exc)
    assert err.retryable is True and "rate limiting" in err.user_message


def test_auth_error_names_the_role_and_is_not_retryable():
    exc = HttpResponseError("forbidden")
    exc.status_code = 403
    err = errors.from_exception("language", exc)
    assert err.retryable is False and "Cognitive Services User" in err.user_message


def test_unknown_exception_is_summarised_without_leaking_its_text():
    err = errors.from_exception("agent", RuntimeError("Bearer eyJSECRET"))
    assert "eyJSECRET" not in err.user_message and "RuntimeError" in err.user_message
