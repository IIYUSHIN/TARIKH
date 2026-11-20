import json

import httpx
import pytest

from app.config import Settings
from app.services.errors import ServiceError
from app.services.speech import AzureSynthesizer, AzureTranscriber

SETTINGS = Settings.from_env({"AZURE_AI_PROJECT_ENDPOINT": "https://res1.services.ai.azure.com/api/projects/p"})


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def _transcriber(handler):
    return AzureTranscriber(SETTINGS, token_provider=lambda: "tok", client=_client(handler))


def _stt_handler(text="my cheque bounced", locales=("en-IN", "hi-IN")):
    seen = {}

    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path.endswith("/transcriptions/locales"):
            return httpx.Response(200, json={"locales": {"fast": list(locales)}})
        seen["url"], seen["auth"], seen["body"] = str(req.url), req.headers["authorization"], req.content
        return httpx.Response(200, json={"combinedPhrases": [{"text": text}]})
    handler.seen = seen
    return handler


def test_transcribe_sends_one_locale_bearer_token_and_returns_text():
    h = _stt_handler("मेरा चेक बाउंस हो गया")
    out = _transcriber(h).transcribe(b"RIFFdata", "audio/wav", "hi-IN")
    assert out == "मेरा चेक बाउंस हो गया"
    assert h.seen["url"].startswith("https://res1.cognitiveservices.azure.com/speechtotext/transcriptions:transcribe")
    assert "api-version=2025-10-15" in h.seen["url"] and h.seen["auth"] == "Bearer tok"
    assert b'"locales": ["hi-IN"]' in h.seen["body"] or b'"locales":["hi-IN"]' in h.seen["body"]


def test_empty_transcript_raises_service_error_with_a_plain_message():
    with pytest.raises(ServiceError, match="No speech") as e:
        _transcriber(_stt_handler(text="")).transcribe(b"RIFF", "audio/wav", "en-IN")
    assert e.value.retryable is False


def test_unsupported_language_message_names_the_language():
    with pytest.raises(ServiceError) as e:
        _transcriber(_stt_handler()).transcribe(b"RIFF", "audio/wav", "pa-IN")
    assert "Punjabi" in e.value.user_message and "pa-IN" in e.value.user_message


def test_supported_locales_accepts_any_json_shape():
    def flat(req):
        return httpx.Response(200, json=["en-IN", "hi-IN", "pa-IN", "not-a-locale"])
    assert _transcriber(flat).supported_locales() == ["en-IN", "hi-IN", "pa-IN"]


def test_http_429_becomes_retryable_service_error():
    def limited(req):
        return httpx.Response(429, text="slow down")
    with pytest.raises(ServiceError) as e:
        _transcriber(limited).supported_locales()
    assert e.value.retryable is True


def test_speak_picks_a_neural_voice_for_the_locale_and_escapes_text():
    posted = {}

    def handler(req):
        if req.url.path.endswith("/voices/list"):
            return httpx.Response(200, json=[
                {"ShortName": "hi-IN-SwaraNeural", "Locale": "hi-IN"},
                {"ShortName": "en-IN-NeerjaNeural", "Locale": "en-IN"}])
        posted["ssml"], posted["ctype"] = req.content.decode(), req.headers["content-type"]
        return httpx.Response(200, content=b"ID3audio")
    audio = AzureSynthesizer(SETTINGS, token_provider=lambda: "tok", client=_client(handler)).speak("Fees < 5 & more", "en-IN")
    assert audio == b"ID3audio" and posted["ctype"].startswith("application/ssml+xml")
    assert "en-IN-NeerjaNeural" in posted["ssml"] and "Fees &lt; 5 &amp; more" in posted["ssml"]


def test_speak_with_no_voice_for_locale_says_so():
    def handler(req):
        return httpx.Response(200, json=[{"ShortName": "en-IN-NeerjaNeural", "Locale": "en-IN"}])
    with pytest.raises(ServiceError, match="pa-IN"):
        AzureSynthesizer(SETTINGS, token_provider=lambda: "tok", client=_client(handler)).speak("hi", "pa-IN")
