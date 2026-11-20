"""Record real service results to disk and play them back later.

Live mode: call the real service, save the result as readable JSON (a "cassette"), return it.
Replay mode: never call out; serve the cassette whose key matches the arguments.
The key is a hash of the arguments, with scan/audio bytes hashed by content and `matter_id`
left out, so the same sample papers replay in a fresh matter. Used to keep a viva demo alive
if the venue network fails, and to capture real evidence for the report.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import typing
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, TypeAdapter

from .errors import ServiceError, from_exception

VOLATILE = {"matter_id"}


def _canon(v: Any) -> Any:
    if isinstance(v, bytes):
        return {"sha256": hashlib.sha256(v).hexdigest()}
    if isinstance(v, BaseModel):
        return json.loads(v.model_dump_json())
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, (list, tuple)):
        return [_canon(i) for i in v]
    if isinstance(v, dict):
        return {k: _canon(x) for k, x in v.items()}
    return v


class Recorder:
    def __init__(self, inner: Any, protocol: type, service: str, cassette_dir: Path | str, mode: str):
        if mode not in ("live", "replay"):
            raise ValueError(f"mode must be 'live' or 'replay', got {mode!r}")
        if mode == "live" and inner is None:
            raise ValueError("live mode needs a real service to call")
        self._inner, self._protocol, self._service, self._mode = inner, protocol, service, mode
        self._dir = Path(cassette_dir) / service
        self._methods = {n for n, _ in inspect.getmembers(protocol, inspect.isfunction)}

    def __getattr__(self, name: str):
        if name.startswith("_") or name not in self._methods:
            raise AttributeError(name)

        def call(*args: Any, **kwargs: Any):
            key = self._key(name, args, kwargs)
            if self._mode == "replay":
                return self._load(name, key)
            try:
                result = getattr(self._inner, name)(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - translated, never swallowed
                raise from_exception(self._service, exc) from exc
            self._save(name, key, result)
            return result

        return call

    # -- helpers -------------------------------------------------------------
    def _key(self, name: str, args: tuple, kwargs: dict) -> str:
        sig = inspect.signature(getattr(self._protocol, name))
        bound = sig.bind(None, *args, **kwargs)  # None stands in for self
        items = {k: _canon(v) for k, v in list(bound.arguments.items())[1:] if k not in VOLATILE}
        digest = hashlib.sha256(json.dumps(items, sort_keys=True, default=str).encode()).hexdigest()[:12]
        return f"{name}-{digest}"

    def _adapter(self, name: str) -> TypeAdapter:
        hints = typing.get_type_hints(getattr(self._protocol, name))
        return TypeAdapter(hints["return"])

    def _save(self, name: str, key: str, result: Any) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        meta = {"service": self._service, "method": name,
                "recorded_at": datetime.now(timezone.utc).isoformat()}
        if isinstance(result, bytes):
            (self._dir / f"{key}.bin").write_bytes(result)
            meta["bytes_file"] = f"{key}.bin"
        else:
            meta["result"] = json.loads(self._adapter(name).dump_json(result))
        (self._dir / f"{key}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load(self, name: str, key: str) -> Any:
        path = self._dir / f"{key}.json"
        if not path.exists():
            raise ServiceError(self._service,
                               "This step was not recorded in the saved run, so it cannot be replayed. "
                               "Use the sample papers from the recorded run, or switch to live mode.")
        meta = json.loads(path.read_text(encoding="utf-8"))
        if "bytes_file" in meta:
            return (self._dir / meta["bytes_file"]).read_bytes()
        return self._adapter(name).validate_python(meta["result"])

    def recorded_at(self) -> str | None:
        """Newest recording time for this service, shown in the replay banner."""
        stamps = [json.loads(p.read_text(encoding="utf-8")).get("recorded_at")
                  for p in self._dir.glob("*.json")] if self._dir.exists() else []
        return max((s for s in stamps if s), default=None)
