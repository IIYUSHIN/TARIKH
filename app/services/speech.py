"""Azure Speech over plain REST with Entra tokens (no native SDK, so it installs on any laptop)."""
from __future__ import annotations

import json
import re
from xml.sax.saxutils import escape

import httpx

from ..config import Settings
from .errors import ServiceError, from_exception

SCOPE = "https://cognitiveservices.azure.com/.default"
STT_VERSION, LOCALES_VERSION = "2025-10-15", "2024-11-15"
LANGUAGE_NAMES = {"en-IN": "English (India)", "hi-IN": "Hindi", "pa-IN": "Punjabi"}
_LOCALE = re.compile(r"^[a-z]{2,3}-[A-Za-z0-9]{2,4}$")


class _Status(Exception):
    def __init__(self, status_code: int):
        super().__init__(str(status_code))
        self.status_code = status_code


def _default_token_provider():
    from azure.identity import DefaultAzureCredential
    cred = DefaultAzureCredential()
    return lambda: cred.get_token(SCOPE).token


class _Base:
    service = "speech"

    def __init__(self, settings: Settings, token_provider=None, client: httpx.Client | None = None):
        self._base = settings.cognitive_base
        self._token = token_provider or _default_token_provider()
        self._http = client or httpx.Client(timeout=90)

    def _send(self, method: str, url: str, **kw) -> httpx.Response:
        try:
            resp = self._http.request(method, url, headers={"Authorization": f"Bearer {self._token()}",
                                                            **kw.pop("headers", {})}, **kw)
        except httpx.TimeoutException as exc:
            raise ServiceError(self.service, "Azure did not answer in time. Check the connection and retry.", True) from exc
        except httpx.TransportError as exc:
            raise ServiceError(self.service, "Could not reach Azure. Check the connection and retry.", True) from exc
        if resp.status_code >= 400:
            raise from_exception(self.service, _Status(resp.status_code))
        return resp


class AzureTranscriber(_Base):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._locales: list[str] | None = None

    def supported_locales(self) -> list[str]:
        if self._locales is None:
            resp = self._send("GET", f"{self._base}/speechtotext/transcriptions/locales",
                              params={"api-version": LOCALES_VERSION})
            found: list[str] = []

            def walk(node):
                if isinstance(node, str):
                    if _LOCALE.match(node) and node not in found:
                        found.append(node)
                elif isinstance(node, dict):
                    for v in node.values():
                        walk(v)
                elif isinstance(node, list):
                    for v in node:
                        walk(v)
            walk(resp.json())
            self._locales = found
        return self._locales

    def transcribe(self, audio: bytes, content_type: str, locale: str) -> str:
        if locale not in self.supported_locales():
            name = LANGUAGE_NAMES.get(locale, locale)
            raise ServiceError(self.service, f"Voice notes in {name} ({locale}) are not available on this Azure "
                                             "resource yet. Choose another language or type the account instead.")
        resp = self._send(
            "POST", f"{self._base}/speechtotext/transcriptions:transcribe",
            params={"api-version": STT_VERSION},
            files={"audio": ("voice-note", audio, content_type)},
            data={"definition": json.dumps({"locales": [locale]})})
        text = " ".join(p.get("text", "") for p in resp.json().get("combinedPhrases", [])).strip()
        if not text:
            raise ServiceError(self.service, "No speech was detected in this recording. Record again closer to the microphone.")
        return text


class AzureSynthesizer(_Base):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._voices: list[dict] | None = None

    def _voice_for(self, locale: str) -> str:
        if self._voices is None:
            self._voices = self._send("GET", f"{self._base}/tts/cognitiveservices/voices/list").json()
        for v in self._voices:
            if v.get("Locale") == locale and v.get("ShortName", "").endswith("Neural"):
                return v["ShortName"]
        raise ServiceError(self.service, f"No spoken voice is available for {locale} on this Azure resource.")

    def speak(self, text: str, locale: str) -> bytes:
        voice = self._voice_for(locale)
        ssml = (f"<speak version='1.0' xml:lang='{locale}'><voice name='{voice}'>{escape(text)}</voice></speak>")
        resp = self._send("POST", f"{self._base}/tts/cognitiveservices/v1",
                          headers={"Content-Type": "application/ssml+xml; charset=utf-8",
                                   "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
                                   "User-Agent": "tarikh"},
                          content=ssml.encode("utf-8"))
        return resp.content
