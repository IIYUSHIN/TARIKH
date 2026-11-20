"""Runtime settings, read once from environment variables (.env is loaded by main)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse


@dataclass(frozen=True)
class Settings:
    mode: Literal["live", "replay"] = "live"
    project_endpoint: str = ""        # https://<resource>.services.ai.azure.com/api/projects/<project>
    model_deployment: str = ""
    cassette_dir: Path = Path("data/cassettes")
    data_dir: Path = Path("data")

    @property
    def resource_name(self) -> str:
        host = urlparse(self.project_endpoint).hostname or ""
        return host.split(".")[0] if host else ""

    @property
    def services_base(self) -> str:
        """Foundry project and Content Understanding."""
        return f"https://{self.resource_name}.services.ai.azure.com" if self.resource_name else ""

    @property
    def cognitive_base(self) -> str:
        """Language and Speech custom-domain endpoint of the same resource."""
        return f"https://{self.resource_name}.cognitiveservices.azure.com" if self.resource_name else ""

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        e = os.environ if env is None else env
        mode = e.get("TARIKH_MODE", "live")
        if mode not in ("live", "replay"):
            raise ValueError(f"TARIKH_MODE must be 'live' or 'replay', got {mode!r}")
        return cls(
            mode=mode,  # type: ignore[arg-type]
            project_endpoint=e.get("AZURE_AI_PROJECT_ENDPOINT", ""),
            model_deployment=e.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", ""),
            cassette_dir=Path(e.get("TARIKH_CASSETTE_DIR", "data/cassettes")),
            data_dir=Path(e.get("TARIKH_DATA_DIR", "data")),
        )
