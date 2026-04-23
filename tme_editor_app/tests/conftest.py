"""Pytest config — ensure editor-app src and sibling packages are importable."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parent
for p in (HERE / "src", REPO / "template_build" / "src", REPO / "moore_build" / "src"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)
