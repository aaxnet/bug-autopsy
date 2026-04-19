"""
tests/test_analyzer.py — Unit tests for Bug Autopsy's core analyser.
"""

import pytest
from autopsy.analyzer import analyze, DiagnosticResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def first_of_type(results: list[DiagnosticResult], error_type: str) -> DiagnosticResult:
    for r in results:
        if r.error_type == error_type:
            return r
    raise AssertionError(f"No result of type {error_type!r} in {[r.error_type for r in results]}")


# ---------------------------------------------------------------------------
# Individual error detection
# ---------------------------------------------------------------------------

class TestModuleNotFoundError:
    def test_detected(self):
        log = "ModuleNotFoundError: No module named 'requests'"
        results = analyze(log)
        r = first_of_type(results, "ModuleNotFoundError")
        assert r.confidence >= 0.90

    def test_fix_mentions_pip(self):
        log = "ModuleNotFoundError: No module named 'requests'"
        r = first_of_type(analyze(log), "ModuleNotFoundError")
        assert any("pip install" in f for f in r.fixes)

    def test_module_name_in_explanation(self):
        log = "ModuleNotFoundError: No module named 'pandas'"
        r = first_of_type(analyze(log), "ModuleNotFoundError")
        assert "pandas" in r.explanation


class TestImportError:
    def test_cannot_import_name(self):
        log = "ImportError: cannot import name 'SessionLocal' from 'db.session'"
        results = analyze(log)
        r = first_of_type(results, "ImportError")
        assert r.confidence >= 0.90
        assert "SessionLocal" in r.explanation

    def test_generic_import_error(self):
        log = "ImportError: DLL load failed while importing _ssl"
        results = analyze(log)
        assert any(r.error_type == "ImportError" for r in results)


class TestKeyError:
    def test_detected(self):
        log = "KeyError: 'user_id'"
        results = analyze(log)
        r = first_of_type(results, "KeyError")
        assert r.confidence >= 0.85

    def test_key_name_in_fixes(self):
        log = "KeyError: 'token'"
        r = first_of_type(analyze(log), "KeyError")
        assert any("token" in f for f in r.fixes)


class TestIndexError:
    def test_detected(self):
        log = "IndexError: list index out of range"
        results = analyze(log)
        r = first_of_type(results, "IndexError")
        assert r.confidence >= 0.90

    def test_fix_mentions_len(self):
        r = first_of_type(analyze("IndexError: list index out of range"), "IndexError")
        assert any("len" in f for f in r.fixes)


class TestTypeError:
    def test_detected(self):
        log = "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
        results = analyze(log)
        r = first_of_type(results, "TypeError")
        assert r.confidence >= 0.85


class TestNameError:
    def test_detected(self):
        log = "NameError: name 'config' is not defined"
        results = analyze(log)
        r = first_of_type(results, "NameError")
        assert "config" in r.explanation
        assert r.confidence >= 0.90


class TestAssertionError:
    def test_detected(self):
        log = "AssertionError"
        results = analyze(log)
        assert any(r.error_type == "AssertionError" for r in results)


class TestPermissionError:
    def test_detected(self):
        log = "PermissionError: [Errno 13] Permission denied: '/etc/passwd'"
        results = analyze(log)
        r = first_of_type(results, "PermissionError")
        assert "/etc/passwd" in r.explanation
        assert r.confidence >= 0.90


class TestTimeoutError:
    def test_detected(self):
        log = "TimeoutError"
        results = analyze(log)
        assert any(r.error_type == "TimeoutError" for r in results)

    def test_requests_timeout(self):
        log = "requests.exceptions.Timeout: HTTPSConnectionPool(host='api.example.com')"
        results = analyze(log)
        assert any(r.error_type == "TimeoutError" for r in results)


# ---------------------------------------------------------------------------
# Additional error types
# ---------------------------------------------------------------------------

class TestAttributeError:
    def test_detected(self):
        log = "AttributeError: 'NoneType' object has no attribute 'split'"
        results = analyze(log)
        r = first_of_type(results, "AttributeError")
        assert "NoneType" in r.explanation
        assert "split" in r.explanation


class TestZeroDivisionError:
    def test_detected(self):
        log = "ZeroDivisionError: division by zero"
        results = analyze(log)
        r = first_of_type(results, "ZeroDivisionError")
        assert r.confidence >= 0.95


class TestFileNotFoundError:
    def test_detected(self):
        log = "FileNotFoundError: [Errno 2] No such file or directory: 'config.json'"
        results = analyze(log)
        r = first_of_type(results, "FileNotFoundError")
        assert "config.json" in r.explanation


class TestRecursionError:
    def test_detected(self):
        log = "RecursionError: maximum recursion depth exceeded"
        results = analyze(log)
        r = first_of_type(results, "RecursionError")
        assert r.confidence >= 0.95


class TestUnicodeDecodeError:
    def test_detected(self):
        log = "UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff"
        results = analyze(log)
        r = first_of_type(results, "UnicodeDecodeError")
        assert "utf-8" in r.explanation


# ---------------------------------------------------------------------------
# Stack frame parsing
# ---------------------------------------------------------------------------

class TestStackFrames:
    TRACEBACK = '''
Traceback (most recent call last):
  File "/app/main.py", line 10, in main
    result = process(data)
  File "/app/processor.py", line 42, in process
    return data["key"]
KeyError: 'key'
'''

    def test_frames_parsed(self):
        results = analyze(self.TRACEBACK)
        r = first_of_type(results, "KeyError")
        assert len(r.frames) >= 1

    def test_frame_line_number(self):
        results = analyze(self.TRACEBACK)
        r = first_of_type(results, "KeyError")
        lines = [f.line for f in r.frames]
        assert 42 in lines


# ---------------------------------------------------------------------------
# Context inference
# ---------------------------------------------------------------------------

class TestContextInference:
    def test_flask_detected(self):
        log = "from flask import Flask\nKeyError: 'token'"
        r = first_of_type(analyze(log), "KeyError")
        assert "Flask" in r.context

    def test_pytest_detected(self):
        log = "def test_login():\n    AssertionError"
        r = first_of_type(analyze(log), "AssertionError")
        assert "Testing" in r.context

    def test_general_fallback(self):
        log = "NameError: name 'x' is not defined"
        r = first_of_type(analyze(log), "NameError")
        assert r.context == "General Python"


# ---------------------------------------------------------------------------
# No-error case
# ---------------------------------------------------------------------------

class TestNoErrors:
    def test_clean_log(self):
        log = "[INFO] Server started on port 8080\n[INFO] All systems nominal."
        results = analyze(log)
        assert results == []


# ---------------------------------------------------------------------------
# Multi-error log
# ---------------------------------------------------------------------------

class TestMultiError:
    MULTI_LOG = """
KeyError: 'database_url'
TypeError: expected str, bytes or os.PathLike object, not NoneType
"""

    def test_multiple_errors_detected(self):
        results = analyze(self.MULTI_LOG)
        types = {r.error_type for r in results}
        assert "KeyError" in types
        assert "TypeError" in types
