"""The Foundry-deployed model: drafts the brief and describes the cheque image.
Code, not the model, decides what is kept: a claim survives only if it cites a real fact id."""
from __future__ import annotations

import base64
import json
from pathlib import Path

from ..config import Settings
from ..models import Brief, Claim, Fact, Observation
from .errors import ServiceError, from_exception

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
SYSTEM_BRIEF = (PROMPTS / "system_brief.md").read_text(encoding="utf-8")
SECTIONS = ["parties", "instrument", "dishonour", "notice", "client_account", "gaps"]
OBSERVATION_KEYS = {"signature": "Signature", "date_written": "Date written", "payee_written": "Payee written",
                    "amount_in_words": "Amount in words", "crossing": "A/c payee crossing"}

BRIEF_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["claims"],
    "properties": {"claims": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["section", "text", "fact_ids"],
        "properties": {"section": {"type": "string", "enum": SECTIONS}, "text": {"type": "string"},
                       "fact_ids": {"type": "array", "items": {"type": "string"}}}}}}}

OBSERVATION_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["observations"],
    "properties": {"observations": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["key", "label", "status", "note"],
        "properties": {"key": {"type": "string", "enum": list(OBSERVATION_KEYS)}, "label": {"type": "string"},
                       "status": {"type": "string", "enum": ["present", "absent", "unclear"]},
                       "note": {"type": "string"}}}}}}

INSPECT_PROMPT = ("You are looking at a photo or scan of a cheque. For each listed item say whether it is visible on the "
                  "cheque. Say 'unclear' if you cannot tell. Describe only what is visible; do not judge validity. "
                  "Items: " + ", ".join(f"{k} ({v})" for k, v in OBSERVATION_KEYS.items()) + ".")


def parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ServiceError("model", "The model's reply could not be read. Please retry.", True) from exc


def validate_brief(raw: dict, facts: list[Fact], has_transcript: bool = False, model: str = "") -> Brief:
    valid = {f.id for f in facts} | ({"transcript"} if has_transcript else set())
    kept, flagged = [], []
    for c in raw.get("claims", []):
        ids = [i for i in c.get("fact_ids", [])]
        if not ids or any(i not in valid for i in ids):
            bad = [i for i in ids if i not in valid]
            why = "no source cited" if not ids else f"cites unknown source {', '.join(bad)}"
            flagged.append(f"Dropped ({why}): {c.get('text', '')}")
            continue
        kept.append(Claim(text=c["text"], fact_ids=ids, section=c.get("section", "")))
    return Brief(claims=kept, flagged=flagged, model=model)


def parse_observations(raw: dict) -> list[Observation]:
    out = []
    for o in raw.get("observations", []):
        if o.get("key") not in OBSERVATION_KEYS:
            continue
        status = o.get("status") if o.get("status") in ("present", "absent", "unclear") else "unclear"
        out.append(Observation(key=o["key"], label=OBSERVATION_KEYS[o["key"]], status=status, note=o.get("note", "")))
    return out


def facts_for_prompt(facts: list[Fact], transcript_redacted: str | None) -> str:
    rows = [{"id": f.id, "label": f.label, "value": f.value, "flag": f.flag} for f in facts]
    text = "FACTS (JSON):\n" + json.dumps(rows, ensure_ascii=False, indent=1)
    if transcript_redacted:
        text += "\n\nCLIENT'S ACCOUNT (id: transcript), personal details already replaced:\n" + transcript_redacted
    return text


class FoundryReasoner:
    """Live implementation of the Reasoner protocol using the Foundry project's OpenAI-style client."""

    def __init__(self, settings: Settings, credential=None):
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
        self._project = AIProjectClient(endpoint=settings.project_endpoint,
                                        credential=credential or DefaultAzureCredential())
        self._openai = self._project.get_openai_client()
        self._model = settings.model_deployment

    def _json_call(self, instructions: str, content, name: str, schema: dict) -> dict:
        try:
            resp = self._openai.responses.create(
                model=self._model, instructions=instructions,
                input=[{"role": "user", "content": content}],
                text={"format": {"type": "json_schema", "name": name, "schema": schema, "strict": True}})
        except Exception as exc:  # noqa: BLE001
            raise from_exception("model", exc) from exc
        return parse_json(resp.output_text)

    def draft_brief(self, facts: list[Fact], transcript_redacted: str | None) -> Brief:
        raw = self._json_call(SYSTEM_BRIEF, [{"type": "input_text", "text": facts_for_prompt(facts, transcript_redacted)}],
                              "case_brief", BRIEF_SCHEMA)
        return validate_brief(raw, facts, has_transcript=bool(transcript_redacted), model=self._model)

    def inspect_cheque_image(self, image: bytes, content_type: str) -> list[Observation]:
        url = f"data:{content_type};base64,{base64.b64encode(image).decode()}"
        raw = self._json_call(INSPECT_PROMPT, [{"type": "input_image", "image_url": url}],
                              "cheque_observations", OBSERVATION_SCHEMA)
        return parse_observations(raw)
