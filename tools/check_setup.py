"""Checks every Azure service Tarikh uses with one real call each, and says in plain words what to fix.

Run:  python -m tools.check_setup
Each check uses the same classes the app uses, so a pass here means the app's own path works.
"""
from __future__ import annotations

import sys
import tempfile
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SAMPLE = ROOT / "samples" / "cheque.png"


def explain(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    low = text.lower()
    if "credentialunavailable" in low or "az login" in low or "defaultazurecredential failed" in low:
        return ("You are not signed in to Azure on this computer. Run `az login`, sign in with the account that owns the "
                "subscription, then run this check again.")
    if "403" in low or "401" in low or "authorization" in low or "permission" in low or "principal" in low:
        return ("Azure refused the call. Your sign-in lacks a role on the resource. In the Azure portal open the Foundry "
                "resource, Access control (IAM), Add role assignment, and give yourself 'Cognitive Services User' and "
                "'Foundry User' (also called Azure AI User). Wait two minutes, then retry.")
    if "deploymentnotfound" in low or "404" in low:
        return ("Azure could not find a model deployment or endpoint. Check that AZURE_AI_MODEL_DEPLOYMENT_NAME in .env "
                "matches the deployment name in the Foundry portal exactly, and that gpt-4.1-mini and text-embedding-3-large "
                "are deployed too.")
    if "429" in low or "ratelimit" in low or "quota" in low:
        return "Azure is rate-limiting this subscription. Wait a minute and retry; if it persists, raise the deployment's tokens-per-minute in Foundry."
    if "name or service not known" in low or "connection" in low or "resolve" in low:
        return "The endpoint in .env could not be reached. Copy AZURE_AI_PROJECT_ENDPOINT again from the Foundry project's Home page."
    return text[:400]


def run() -> int:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    from app.config import Settings
    s = Settings.from_env()
    results: list[tuple[str, bool, str]] = []

    def check(name: str, fn) -> None:
        t0 = time.time()
        try:
            detail = fn()
            results.append((name, True, f"{detail} ({time.time() - t0:.1f}s)"))
        except Exception as exc:  # noqa: BLE001  a checker must report every failure, not stop at the first
            results.append((name, False, explain(exc)))
        r = results[-1]
        print(f"{'PASS' if r[1] else 'FAIL'}  {r[0]}\n      {r[2]}\n", flush=True)

    if not s.project_endpoint or not s.model_deployment:
        print("FAIL  Settings\n      .env is missing AZURE_AI_PROJECT_ENDPOINT or AZURE_AI_MODEL_DEPLOYMENT_NAME. "
              "Copy .env.example to .env and fill both in (docs/azure-setup.md, step 7).")
        return 1
    print(f"Project endpoint: {s.project_endpoint}\nModel deployment: {s.model_deployment}\n")

    from azure.identity import DefaultAzureCredential
    cred = DefaultAzureCredential()
    check("Sign-in (az login)", lambda: (cred.get_token("https://cognitiveservices.azure.com/.default"), "signed in")[1])

    def model():
        from azure.ai.projects import AIProjectClient
        client = AIProjectClient(endpoint=s.project_endpoint, credential=cred).get_openai_client()
        r = client.responses.create(model=s.model_deployment, input="Reply with the single word: ready")
        return f"{s.model_deployment} answered: {r.output_text.strip()[:30]!r}"
    check("Foundry model deployment", model)

    def content():
        from app.models import DocType
        from app.services.extraction import ContentUnderstandingExtractor, ModelExtractor
        reader = ModelExtractor(s, credential=cred) if s.extractor == "model" else ContentUnderstandingExtractor(s, credential=cred)
        facts = reader.extract(DocType.CHEQUE, SAMPLE.read_bytes(), "image/png")
        read = {f.key: f.value for f in facts if f.value}
        if "cheque_number" not in read:
            raise RuntimeError(f"the analyzer ran but read no cheque number; got {read}")
        return f"read {len(read)} fields from the sample cheque, cheque number {read['cheque_number']}"
    check("Paper reading (" + ("the model" if s.extractor == "model" else "Content Understanding") + ") reads the sample cheque", content)

    def language():
        from app.services.language import AzureTextAnalyzer
        out = AzureTextAnalyzer(s, credential=cred).redact_pii("My cheque bounced, call me on 98765 43210", "en")
        if "98765" in out.redacted_text:
            raise RuntimeError("the phone number was not masked: " + out.redacted_text)
        return f"masked: {out.redacted_text!r}"
    check("Language masks personal details", language)

    audio: dict[str, bytes] = {}

    def speak():
        from app.services.speech import AzureSynthesizer
        audio["mp3"] = AzureSynthesizer(s).speak("The cheque number is four seven one eight.", "en-IN")
        return f"synthesised {len(audio['mp3'])} bytes of speech"
    check("Speech speaks (text to speech)", speak)

    def listen():
        from app.services.speech import AzureTranscriber
        t = AzureTranscriber(s)
        locales = t.supported_locales()
        text = t.transcribe(audio["mp3"], "audio/mpeg", "en-IN") if "mp3" in audio else "(skipped: speech output failed)"
        have = ", ".join(l for l in ("en-IN", "hi-IN", "pa-IN") if l in locales) or "none of en-IN, hi-IN, pa-IN"
        return f"heard back: {text!r}. Offered here: {have}"
    check("Speech listens (fast transcription)", listen)

    def agent():
        from app.services.agent import FoundryAssistant
        from app.store import Store
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "check.db")
            m = store.create_matter("setup check")
            a = FoundryAssistant(s, store, credential=cred, today=lambda: date(2026, 11, 21)).ask("What is the cheque number?", m.id)
            return f"agent answered after {len(a.tool_calls)} tool call(s): {a.text[:60]!r}"
    check("Foundry agent with tools", agent)

    failed = [r for r in results if not r[1]]
    print("All checks passed. You can run the app." if not failed else f"{len(failed)} of {len(results)} checks failed. Fix the first FAIL above, then run this again.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(run())
