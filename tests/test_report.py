"""
tests/test_report.py — Unit tests for Bug Autopsy's Markdown report generator.
"""

import pytest
from autopsy.analyzer import analyze, DiagnosticResult
from autopsy import report as report_mod


def _make_result(**kwargs) -> DiagnosticResult:
    defaults = dict(
        error_type="KeyError",
        message="KeyError: 'token'",
        confidence=0.93,
        explanation="The key 'token' was not found.",
        fixes=["Use .get()", "Add a guard"],
        context="General Python",
        frames=[],
        raw_excerpt="",
    )
    defaults.update(kwargs)
    return DiagnosticResult(**defaults)


class TestReportGeneration:
    def test_header_present(self):
        md = report_mod.generate([], source_label="test.log")
        assert "Bug Autopsy Report" in md

    def test_no_errors_message(self):
        md = report_mod.generate([])
        assert "No Errors Detected" in md

    def test_error_type_in_report(self):
        r = _make_result()
        md = report_mod.generate([r])
        assert "KeyError" in md

    def test_explanation_in_report(self):
        r = _make_result(explanation="Custom explanation text.")
        md = report_mod.generate([r])
        assert "Custom explanation text." in md

    def test_fixes_in_report(self):
        r = _make_result(fixes=["Fix A", "Fix B", "Fix C"])
        md = report_mod.generate([r])
        assert "Fix A" in md
        assert "Fix C" in md

    def test_toc_present_for_multiple(self):
        r1 = _make_result(error_type="KeyError")
        r2 = _make_result(error_type="TypeError", message="TypeError: bad type")
        md = report_mod.generate([r1, r2])
        assert "Table of Contents" in md

    def test_toc_absent_for_single(self):
        r = _make_result()
        md = report_mod.generate([r], include_toc=True)
        # TOC only added when len(results) > 1
        assert "Table of Contents" not in md

    def test_source_label_in_report(self):
        r = _make_result()
        md = report_mod.generate([r], source_label="/path/to/error.log")
        assert "/path/to/error.log" in md

    def test_confidence_percentage_shown(self):
        r = _make_result(confidence=0.95)
        md = report_mod.generate([r])
        assert "95%" in md

    def test_raw_excerpt_in_report(self):
        r = _make_result(raw_excerpt="some raw log excerpt here")
        md = report_mod.generate([r])
        assert "some raw log excerpt here" in md

    def test_save_writes_file(self, tmp_path):
        path = str(tmp_path / "out.md")
        content = "# Test"
        report_mod.save(content, path)
        with open(path) as f:
            assert f.read() == content


class TestEndToEndReport:
    """Full pipeline: text → analyze → report."""

    LOG = """
Traceback (most recent call last):
  File "/app/app.py", line 5, in get
    return data["user"]
KeyError: 'user'
"""

    def test_end_to_end(self):
        results = analyze(self.LOG)
        md = report_mod.generate(results, source_label="app.log")
        assert "KeyError" in md
        assert "Recommended Fixes" in md
        assert "Explanation" in md
