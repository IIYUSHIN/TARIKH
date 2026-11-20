"""Starts Tarikh on port 8765 with test doubles and a fixed clock (21 Nov 2026), for browser tests and screenshots.
Test-only: the doubles never ship as product behaviour."""
import sys
from datetime import date
from pathlib import Path

import uvicorn

from app.analyzers import FIELD_SPECS
from app.main import create_app
from app.models import Fact, SourceRef, doc_id_for
from app.pipeline import Pipeline, Services
from app.store import Store
from tests.doubles import DEFAULTS, FakeAnalyzer, FakeAssistant, FakeReasoner, FakeSynth, FakeTranscriber

BOX = {  # rough regions on the sample papers, only so the highlight can be exercised
    "cheque_number": [.06, .08, .30, .08, .30, .14, .06, .14], "cheque_date": [.70, .10, .92, .10, .92, .17, .70, .17],
    "amount_figures": [.70, .42, .92, .42, .92, .52, .70, .52], "drawer_name": [.52, .62, .92, .62, .92, .72, .52, .72],
    "payee_name": [.10, .26, .60, .26, .60, .34, .10, .34], "bank_name": [.06, .02, .50, .02, .50, .07, .06, .07],
}


class UiExtractor:
    def extract(self, doc_type, content, content_type):
        did = doc_id_for(content)
        out = []
        for i, s in enumerate(FIELD_SPECS[doc_type]):
            val = None if s.manual else DEFAULTS.get(s.key)
            low = s.key == "return_date"
            out.append(Fact(id=f"{did}-{s.key}", doc_id=did, key=s.key, label=s.label, value=val, manual=s.manual,
                            confidence=None if s.manual else (0.58 if low else 0.93 - i * 0.01),
                            flag="Two dates were found near this. Check against the paper." if low else None,
                            source=SourceRef(doc_id=did, polygon=BOX[s.key]) if s.key in BOX else None))
        return out


def build(db: Path) -> object:
    store = Store(db)
    svc = Services(UiExtractor(), FakeTranscriber("My cheque bounced. Call me on 98765 43210."), FakeSynth(), FakeAnalyzer(), FakeReasoner(), FakeAssistant())
    pipe = Pipeline(store, svc, db.parent / "data", today=lambda: date(2026, 11, 21))
    return create_app(pipe, store, db.parent / "data", "live", lambda: None, "gpt-4.1")


if __name__ == "__main__":
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    uvicorn.run(build(tmp / "ui.db"), host="127.0.0.1", port=int(sys.argv[1]) if len(sys.argv) > 1 else 8765, log_level="warning")
