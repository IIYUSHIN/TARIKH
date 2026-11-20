"""Runtime settings, read once from environment variables (.env is loaded by main)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class Settings:
    mode: Literal["live", "replay"] = "live"
    project_endpoint: str = ""        # https://<resource>.services.ai.azure.com/api/projects/<project>
    services_endpoint: str = ""       # https://<resource>.services.ai.azure.com  (Language, Content Understanding)
    speech_region: str = ""
    model_deployment: str = ""
    cassette_dir: Path = Path("data/cassettes")
    data_dir: Path = Path("data")

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        e = os.environ if env is None else env
        mode = e.get("TARIKH_MODE", "live")
        if mode not in ("live", "replay"):
            raise ValueError(f"TARIKH_MODE must be 'live' or 'replay', got {mode!r}")
        return cls(
            mode=mode,  # type: ignore[arg-type]
            project_endpoint=e.get("AZURE_AI_PROJECT_ENDPOINT", ""),
            services_endpoint=e.get("AZURE_AI_SERVICES_ENDPOINT", ""),
            speech_region=e.get("AZURE_SPEECH_REGION", ""),
            model_deployment=e.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", ""),
            cassette_dir=Path(e.get("TARIKH_CASSETTE_DIR", "data/cassettes")),
            data_dir=Path(e.get("TARIKH_DATA_DIR", "data")),
        )
