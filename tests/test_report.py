"""Checks that REPORT.md is filled in. It does not grade your reasoning: it makes sure nothing is left blank."""
import pathlib
import re

REPORT = pathlib.Path(__file__).resolve().parent.parent / "REPORT.md"


def section(text, start, end=None):
    i = text.index(start)
    j = text.index(end, i) if end else len(text)
    return text[i:j]


def test_report_exists():
    assert REPORT.exists(), "REPORT.md is missing."


def test_required_answers_filled():
    text = REPORT.read_text(encoding="utf-8")
    required = section(text, "## Part A", "**Going further")
    left = required.count("TODO")
    assert left == 0, f"{left} required answer(s) still say TODO in REPORT.md (Parts A and B)."


def test_a3_names_the_bottleneck():
    text = REPORT.read_text(encoding="utf-8")
    a3 = section(text, "Explain in two or three sentences.", "**A4.**")  # your answer, not the question
    assert re.search(r"provider|rate.?limit|quota", a3, re.I), (
        "A3: where is the bottleneck in case 3? Think about who makes the analyses slower, and what more copies change."
    )


def test_b2_explains_the_fast_rebuild():
    text = REPORT.read_text(encoding="utf-8")
    b2 = section(text, "- First build:", "**B3.**")  # your answer, not the question
    assert re.search(r"\bcache", b2, re.I), (
        "B2: why is the second build so short? Name the mechanism Docker uses to skip the steps that did not change."
    )
