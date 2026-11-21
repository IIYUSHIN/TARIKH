"""Content Understanding: read a cheque, return memo or demand notice into source-linked facts."""
from __future__ import annotations

import re
from datetime import date

from ..analyzers import FIELD_SPECS, FieldSpec, analyzer_id, build_analyzer_definition
from ..config import Settings
from ..models import DocType, Fact, SourceRef, doc_id_for

_SOURCE = re.compile(r"D\((\d+),([^)]*)\)")
NOT_READ = "Not read from the paper. Enter it."
AMBIGUOUS = "Day and month could be read either way; confirm against the paper."


def _value(raw: dict) -> str | None:
    for k in ("valueString", "valueDate", "valueNumber", "valueInteger"):
        v = raw.get(k)
        if v is not None:
            if isinstance(v, float) and v.is_integer():
                v = int(v)
            return str(v)
    return None


def _polygon(source: str | None, pages: list[dict]) -> SourceRef | None:
    m = _SOURCE.search(source or "")
    if not m:
        return None
    page_no = int(m.group(1))
    nums = [float(x) for x in m.group(2).split(",") if x.strip()]
    page = next((p for p in pages if p.get("pageNumber") == page_no), None)
    if not page or not page.get("width") or not page.get("height") or len(nums) < 6:
        return None
    w, h = float(page["width"]), float(page["height"])
    poly = [round(n / (w if i % 2 == 0 else h), 4) for i, n in enumerate(nums)]
    return SourceRef(doc_id="", page=page_no, polygon=poly)


def _ambiguous(value: str) -> bool:
    try:
        d = date.fromisoformat(value)
    except ValueError:
        return False
    return d.day <= 12 and d.month <= 12 and d.day != d.month


def map_result(doc_type: DocType, raw: dict, doc_id: str) -> list[Fact]:
    """Pure conversion of an analysis result (REST-shaped dict) into Facts. Never guesses."""
    content = (raw.get("contents") or [{}])[0]
    fields, pages = content.get("fields") or {}, content.get("pages") or []
    facts: list[Fact] = []
    for spec in FIELD_SPECS[doc_type]:
        fid = f"{doc_id}-{spec.key}"
        if spec.manual:
            facts.append(Fact(id=fid, doc_id=doc_id, key=spec.key, label=spec.label,
                              manual=True, flag=spec.manual_hint))
            continue
        f = fields.get(spec.key) or {}
        value, conf = _value(f), f.get("confidence")
        src = _polygon(f.get("source"), pages)
        if src:
            src.doc_id = doc_id
        flag = None
        if value is None:
            flag = NOT_READ
        elif spec.type == "date" and _ambiguous(value):
            flag, conf = AMBIGUOUS, min(conf if conf is not None else 0.6, 0.6)
        facts.append(Fact(id=fid, doc_id=doc_id, key=spec.key, label=spec.label,
                          value=value, confidence=conf, source=src, flag=flag))
    return facts


class ContentUnderstandingExtractor:
    """Live implementation of the Extractor protocol."""

    def __init__(self, settings: Settings, credential=None, client=None):
        if client is None:
            from azure.ai.contentunderstanding import ContentUnderstandingClient
            from azure.identity import DefaultAzureCredential
            client = ContentUnderstandingClient(
                endpoint=settings.services_base, credential=credential or DefaultAzureCredential())
        self._client = client
        self._settings = settings
        self._defaults_set = False
        self._ready: set[DocType] = set()

    def ensure_analyzer(self, doc_type: DocType) -> None:
        if not self._defaults_set:  # the resource must know which deployments back each model name before any analysis
            self.configure_defaults(self._settings.model_deployment, self._settings.cu_mini_deployment,
                                    self._settings.cu_embedding_deployment)
            self._defaults_set = True
        if doc_type in self._ready:
            return
        self._client.begin_create_analyzer(
            analyzer_id(doc_type), build_analyzer_definition(doc_type), allow_replace=True).result()
        self._ready.add(doc_type)

    def configure_defaults(self, completion: str, mini: str, embedding: str) -> None:
        """One-time mapping of model names to the user's deployment names."""
        self._client.update_defaults(model_deployments={
            "gpt-4.1": completion, "gpt-4.1-mini": mini, "text-embedding-3-large": embedding})

    def extract(self, doc_type: DocType, content: bytes, content_type: str) -> list[Fact]:
        self.ensure_analyzer(doc_type)
        result = self._client.begin_analyze_binary(
            analyzer_id(doc_type), binary_input=content, content_type=content_type).result()
        return map_result(doc_type, result.as_dict(), doc_id_for(content))


class ModelExtractor:
    """For regions without Content Understanding (for example South India): the deployed vision model reads the
    paper into the same fields. No polygons come back, so each fact says it was read by the model, not boxed."""

    def __init__(self, settings: Settings, credential=None):
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
        self._openai = AIProjectClient(endpoint=settings.project_endpoint,
                                       credential=credential or DefaultAzureCredential()).get_openai_client()
        self._model = settings.model_deployment

    def extract(self, doc_type: DocType, content: bytes, content_type: str) -> list[Fact]:
        import base64
        import json as _json
        from .errors import from_exception
        specs = [s for s in FIELD_SPECS[doc_type] if not s.manual]
        schema = {"type": "object", "additionalProperties": False, "required": ["fields"], "properties": {"fields": {
            "type": "object", "additionalProperties": False, "required": [s.key for s in specs],
            "properties": {s.key: {"type": ["string", "null"], "description": s.description} for s in specs}}}}
        if content_type == "application/pdf":
            part = {"type": "input_file", "filename": "paper.pdf",
                    "file_data": "data:application/pdf;base64," + base64.b64encode(content).decode()}
        else:
            part = {"type": "input_image", "image_url": f"data:{content_type};base64," + base64.b64encode(content).decode()}
        prompt = ("Read this Indian banking paper. Return each field exactly as printed. Dates as YYYY-MM-DD "
                  "(Indian papers write the day first). Amounts as digits only. Use null when a field is not visible; never guess.")
        try:
            resp = self._openai.responses.create(model=self._model, instructions=prompt,
                                                 input=[{"role": "user", "content": [part]}],
                                                 text={"format": {"type": "json_schema", "name": "paper", "schema": schema, "strict": True}})
            fields = _json.loads(resp.output_text)["fields"]
        except Exception as exc:  # noqa: BLE001
            raise from_exception("extraction", exc) from exc
        doc_id = doc_id_for(content)
        raw = {"contents": [{"fields": {k: ({"valueString": v, "confidence": None} if v else {}) for k, v in fields.items()}}]}
        facts = map_result(doc_type, raw, doc_id)
        for f in facts:
            if f.value and not f.manual and not f.flag:
                f.flag = "Read by the model without a location box. Check it against the paper."
        return facts
