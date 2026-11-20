"""The single Foundry agent the advocate can question. It can only call two tools, both read-only and
both bound to the matter being discussed, so a question can never reach another matter."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Callable

from ..config import Settings
from ..matter_dates import fact_value, window_dict, windows_for_matter
from ..models import Answer, ToolCall
from ..store import Store
from .errors import ServiceError, from_exception

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
AGENT_NAME = "tarikh-case-desk"


def agent_instructions() -> str:
    return (PROMPTS / "system_agent.md").read_text(encoding="utf-8") + "\n\nLEGAL REFERENCE\n" + \
           (PROMPTS / "statute_digest.md").read_text(encoding="utf-8")


TOOL_SPECS = [
    {"name": "get_deadlines",
     "description": "Statutory windows for this matter (cheque validity, demand notice, drawer's time to pay, complaint), "
                    "computed by the deadline engine as of today.",
     "parameters": {"type": "object", "properties": {}, "additionalProperties": False, "required": []}},
    {"name": "get_fact",
     "description": "One fact read from this matter's papers, by key (for example cheque_number, cheque_date, amount_figures, "
                    "drawer_name, payee_name, return_reason, notice_date).",
     "parameters": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"],
                    "additionalProperties": False}},
]


class ToolRegistry:
    def __init__(self, store: Store, matter_id: str, today: Callable[[], date] = date.today):
        self._store, self._matter_id, self._today = store, matter_id, today

    def call(self, name: str, args: dict) -> dict:
        matter = self._store.get_matter(self._matter_id)   # always the bound matter; model arguments cannot change it
        if name == "get_deadlines":
            today = self._today()
            return {"as_of": today.isoformat(), "windows": [window_dict(w) for w in windows_for_matter(matter, today)]}
        if name == "get_fact":
            key = str(args.get("key", ""))
            for d in matter.documents:
                for f in d.facts:
                    if f.key == key:
                        return {"key": key, "label": f.label, "value": f.value, "flag": f.flag,
                                "document": d.doc_type.value}
            return {"error": f"no fact named {key!r} in this matter"}
        raise ValueError(f"unknown tool {name!r}")


def run_tool_loop(create: Callable, question: str, registry: ToolRegistry, max_rounds: int = 4) -> Answer:
    """create(input) -> response. Runs the model's function calls locally until it answers in text."""
    recorded: list[ToolCall] = []
    response = create(question)
    for _ in range(max_rounds):
        calls = [i for i in response.output if getattr(i, "type", None) == "function_call"]
        if not calls:
            return Answer(text=response.output_text, tool_calls=recorded)
        outputs = []
        for c in calls:
            try:
                args = json.loads(c.arguments or "{}")
            except json.JSONDecodeError:
                args = None
            if not isinstance(args, dict):
                result = {"error": "arguments were not valid JSON"}
            else:
                try:
                    result = registry.call(c.name, args)
                except ValueError as exc:
                    result = {"error": str(exc)}
            recorded.append(ToolCall(name=c.name, args=args if isinstance(args, dict) else {}, result=result))
            outputs.append({"type": "function_call_output", "call_id": c.call_id, "output": json.dumps(result)})
        response = create(outputs)
    raise ServiceError("agent", "The assistant took too many steps without answering. Please rephrase and retry.", True)


class FoundryAssistant:
    """Live implementation of the Assistant protocol."""

    def __init__(self, settings: Settings, store: Store, credential=None, today: Callable[[], date] = date.today):
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
        self._project = AIProjectClient(endpoint=settings.project_endpoint,
                                        credential=credential or DefaultAzureCredential())
        self._openai = self._project.get_openai_client()
        self._model, self._store, self._today = settings.model_deployment, store, today
        self._ready = False

    def ensure_agent(self) -> None:
        if self._ready:
            return
        from azure.ai.projects.models import FunctionTool, PromptAgentDefinition
        tools = [FunctionTool(name=t["name"], description=t["description"], parameters=t["parameters"], strict=True)
                 for t in TOOL_SPECS]
        self._project.agents.create_version(
            agent_name=AGENT_NAME,
            definition=PromptAgentDefinition(model=self._model, instructions=agent_instructions(), tools=tools))
        self._ready = True

    def ask(self, question: str, matter_id: str) -> Answer:
        try:
            self.ensure_agent()
            conversation = self._openai.conversations.create()
            ref = {"agent_reference": {"name": AGENT_NAME, "type": "agent_reference"}}

            def create(inp):
                return self._openai.responses.create(conversation=conversation.id, input=inp, extra_body=ref)

            return run_tool_loop(create, question, ToolRegistry(self._store, matter_id, self._today))
        except ServiceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise from_exception("agent", exc) from exc
