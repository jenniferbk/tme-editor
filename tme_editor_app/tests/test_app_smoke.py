"""The Streamlit page renders without raising (no Gemini call involved)."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_app_renders_without_exception():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
    headers = " ".join(h.value for h in at.header)
    assert "Phase 1" in headers and "Phase 2" in headers


def test_start_over_bumps_the_uploader_epoch():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert at.session_state["uploader_epoch"] == 0
    at.sidebar.button[0].click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.session_state["uploader_epoch"] == 1
