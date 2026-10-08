"""Gemini output parsing is strict about shape and honest about gaps."""
import json

from classifier import parse_classifications


def _raw(items):
    return json.dumps({"classifications": items})


def test_complete_valid_reply():
    labels, report = parse_classifications(_raw([{"i": 1, "label": "heading_1"}, {"i": 2, "label": "body"}]), 2)
    assert labels == ["heading_1", "body"]
    assert report == {"missing": 0, "invalid": 0, "duplicates": 0}


def test_missing_and_invalid_are_counted_not_hidden():
    labels, report = parse_classifications(_raw([{"i": 1, "label": "nonsense"}]), 3)
    assert labels == ["body", "body", "body"]
    assert report == {"missing": 2, "invalid": 1, "duplicates": 0}


def test_duplicate_indices_count_once_and_last_wins():
    labels, report = parse_classifications(_raw([{"i": 1, "label": "body"}, {"i": 1, "label": "heading_2"}]), 1)
    assert labels == ["heading_2"]
    assert report["duplicates"] == 1 and report["missing"] == 0


def test_garbage_items_are_invalid_not_fatal():
    labels, report = parse_classifications(_raw([{"i": "x", "label": "body"}, "junk"]), 1)
    assert labels == ["body"] and report["invalid"] == 2 and report["missing"] == 1
