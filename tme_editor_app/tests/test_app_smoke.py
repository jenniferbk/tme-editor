"""The Streamlit page renders without raising (no Gemini call involved)."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_app_renders_without_exception():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
    headers = " ".join(h.value for h in at.header)
    assert "Phase 1" in headers and "Phase 2" in headers
