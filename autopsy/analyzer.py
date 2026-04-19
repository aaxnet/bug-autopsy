"""
analyzer.py — Core parsing, detection, and classification logic for Bug Autopsy.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class StackFrame:
    file: str
    line: int
    function: str
    source: str = ""


@dataclass
class DiagnosticResult:
    error_type: str
    message: str
    confidence: float          # 0.0 – 1.0
    explanation: str
    fixes: list[str]
    context: str               # inferred environment (e.g. "Flask", "pytest")
    frames: list[StackFrame] = field(default_factory=list)
    raw_excerpt: str = ""


# ---------------------------------------------------------------------------
# Known error patterns
# ---------------------------------------------------------------------------

# Each entry: (regex pattern, error_type, base_confidence, explanation_template, fixes)
_ERROR_PATTERNS: list[tuple] = [
    (
        r"ModuleNotFoundError: No module named '([^']+)'",
        "ModuleNotFoundError",
        0.97,
        "Python could not find the module '{match}'. It is either not installed in the current environment or the module name is misspelled.",
        [
            "Install the missing package: `pip install {match}`",
            "If inside a virtual environment, make sure it is activated: `source .venv/bin/activate`",
            "Check for typos in the import statement — Python module names are case-sensitive.",
            "If you installed the package but still see this error, verify the Python interpreter being used: `which python` / `python --version`.",
        ],
    ),
    (
        r"ImportError: cannot import name '([^']+)' from '([^']+)'",
        "ImportError",
        0.95,
        "The name '{match}' does not exist in module '{match2}'. It may have been renamed, removed, or never existed in this version.",
        [
            "Check the installed version of '{match2}' — the API may have changed: `pip show {match2}`.",
            "Review the official documentation or changelog for the correct import path.",
            "Search the package source for the correct symbol name.",
            "Pin to a compatible version if a recent upgrade broke the import.",
        ],
    ),
    (
        r"ImportError: (.+)",
        "ImportError",
        0.88,
        "An import failed: {match}. This usually indicates a missing dependency, a circular import, or a broken package installation.",
        [
            "Reinstall the package: `pip install --force-reinstall <package>`",
            "Check for circular imports between your own modules.",
            "Inspect the traceback above this error for the originating import.",
        ],
    ),
    (
        r"KeyError: '?([^'\n]+)'?",
        "KeyError",
        0.93,
        "The key '{match}' was not found in the dictionary. The data structure does not contain this key at the time of access.",
        [
            "Use `.get()` with a default: `value = d.get('{match}', default_value)`",
            "Check for typos in the key name — keys are case-sensitive.",
            "Verify that the key is populated before access (e.g. API response may vary).",
            "Add a guard: `if '{match}' in d:` before accessing.",
        ],
    ),
    (
        r"IndexError: list index out of range",
        "IndexError",
        0.96,
        "An attempt was made to access a list element at an index that does not exist. The list is shorter than expected.",
        [
            "Check the length before indexing: `if len(lst) > idx:`",
            "Ensure the upstream data source returns the expected number of elements.",
            "Use `enumerate()` or iterate instead of manual index arithmetic.",
            "Consider using slicing (`lst[i:i+1]`) to safely get zero-or-one element.",
        ],
    ),
    (
        r"TypeError: (.+)",
        "TypeError",
        0.90,
        "A type mismatch occurred: {match}. An operation was applied to a value of an incompatible type.",
        [
            "Inspect the types involved with `type(value)` or `print(repr(value))`.",
            "Add explicit type conversion where needed (e.g. `int()`, `str()`, `list()`).",
            "Check function signatures — a required argument may have been omitted.",
            "If using an API or library, confirm the expected parameter types in its documentation.",
        ],
    ),
    (
        r"NameError: name '([^']+)' is not defined",
        "NameError",
        0.95,
        "The name '{match}' is referenced before it has been defined in the current scope.",
        [
            "Define or import '{match}' before the line that uses it.",
            "Check for typos — Python is case-sensitive.",
            "If '{match}' is a built-in or standard-library name, make sure you haven't accidentally shadowed it.",
            "Verify you are not referencing a variable outside its scope (e.g. a local variable used at module level).",
        ],
    ),
    (
        r"AssertionError",
        "AssertionError",
        0.85,
        "An `assert` statement evaluated to False. The program's invariants were not satisfied at this point.",
        [
            "Inspect the failing assertion and the values involved — add `assert condition, f'Got {value}'` for context.",
            "Trace back to where the asserted variable is set to understand why it has an unexpected value.",
            "If this is a test, review the expected vs actual values carefully.",
            "Consider replacing bare asserts with explicit checks and meaningful error messages.",
        ],
    ),
    (
        r"PermissionError: \[Errno 13\] Permission denied: '([^']+)'",
        "PermissionError",
        0.96,
        "The process does not have permission to access '{match}'. This is an OS-level file-system restriction.",
        [
            "Check file/directory ownership and permissions: `ls -la {match}`",
            "Run with appropriate privileges — but avoid `sudo` for application code if possible.",
            "Ensure the running user has read/write access to the target path.",
            "If writing to a system directory, redirect output to a user-writable location instead.",
        ],
    ),
    (
        r"TimeoutError|concurrent\.futures\.TimeoutError|socket\.timeout|requests\.exceptions\.Timeout",
        "TimeoutError",
        0.88,
        "An operation exceeded its time limit. This typically indicates network latency, an unresponsive service, or an overly short timeout threshold.",
        [
            "Increase the timeout value in the relevant client or connection configuration.",
            "Add retry logic with exponential backoff for transient timeouts.",
            "Check whether the target service/host is reachable and responding.",
            "Profile the slow operation to see if it can be optimised rather than worked around.",
        ],
    ),
    (
        r"RecursionError: maximum recursion depth exceeded",
        "RecursionError",
        0.97,
        "The call stack grew deeper than Python's recursion limit (default 1 000). A recursive function is not terminating as expected.",
        [
            "Identify the base case of the recursion and verify it is reachable with the current input.",
            "Convert deep recursion to an iterative approach using an explicit stack.",
            "Temporarily increase the limit to diagnose: `sys.setrecursionlimit(5000)` — but fix the root cause.",
            "Use memoisation or dynamic programming to avoid redundant recursive calls.",
        ],
    ),
    (
        r"AttributeError: '([^']+)' object has no attribute '([^']+)'",
        "AttributeError",
        0.93,
        "The object of type '{match}' does not have an attribute named '{match2}'. This often means the wrong type was received or a method/property was renamed.",
        [
            "Use `dir(obj)` or `help(obj)` to inspect available attributes.",
            "Verify the object is of the type you expect with `type(obj)` / `isinstance()`.",
            "Check library version — the attribute may have been renamed in an update.",
            "Ensure you haven't shadowed the class name with a variable of a different type.",
        ],
    ),
    (
        r"ZeroDivisionError: division by zero",
        "ZeroDivisionError",
        0.98,
        "A division by zero occurred. The denominator evaluated to 0 at runtime.",
        [
            "Add a guard before the division: `result = a / b if b != 0 else fallback`",
            "Trace back where the denominator is computed to understand why it can be zero.",
            "Consider using `math.isclose(b, 0)` for float denominators.",
        ],
    ),
    (
        r"FileNotFoundError: \[Errno 2\] No such file or directory: '([^']+)'",
        "FileNotFoundError",
        0.97,
        "The file or directory '{match}' does not exist at the given path.",
        [
            "Verify the path is correct relative to the working directory: `os.getcwd()`",
            "Use `pathlib.Path.exists()` to check before opening.",
            "If the path is user-supplied, validate and sanitise it early.",
            "Ensure the file was created by a prior step before this code runs.",
        ],
    ),
    (
        r"ValueError: (.+)",
        "ValueError",
        0.87,
        "A value with the correct type but an inappropriate value was passed: {match}.",
        [
            "Validate input values before passing them to the failing function.",
            "Check the function's documentation for acceptable value ranges or formats.",
            "Add informative error messages to help identify the invalid value at runtime.",
        ],
    ),
    (
        r"OSError: (.+)",
        "OSError",
        0.82,
        "An OS-level error occurred: {match}.",
        [
            "Check system resources (disk space, open file descriptors, memory).",
            "Verify paths, permissions, and that required system services are running.",
            "Wrap in try/except OSError to handle gracefully and log the errno.",
        ],
    ),
    (
        r"StopIteration",
        "StopIteration",
        0.80,
        "A StopIteration was raised outside of a generator/iterator context. This can happen when `next()` is called on an exhausted iterator.",
        [
            "Provide a default to `next()`: `next(iterator, None)`",
            "Check that the iterator/generator is not exhausted before calling `next()`.",
            "If inside a generator, ensure `StopIteration` is not accidentally raised (use `return` instead in Python 3.7+).",
        ],
    ),
    (
        r"RuntimeError: (.+)",
        "RuntimeError",
        0.78,
        "A runtime error occurred: {match}. This is a general-purpose exception often raised when no more specific category fits.",
        [
            "Read the full message carefully — it usually describes the exact condition.",
            "Check for thread-safety issues if using concurrency.",
            "Review library documentation for this specific RuntimeError message.",
        ],
    ),
    (
        r"UnicodeDecodeError: '([^']+)' codec can't decode",
        "UnicodeDecodeError",
        0.94,
        "A byte sequence could not be decoded using the '{match}' codec. The file or data stream likely uses a different encoding.",
        [
            "Specify the correct encoding when opening the file: `open(path, encoding='utf-8')`",
            "Use `errors='replace'` or `errors='ignore'` as a temporary workaround.",
            "Detect the encoding automatically with the `chardet` library: `pip install chardet`",
            "Ensure the data source (API, file, DB) is configured to use a consistent encoding.",
        ],
    ),
    (
        r"MemoryError",
        "MemoryError",
        0.90,
        "The process ran out of available memory. The operation attempted to allocate more RAM than is available.",
        [
            "Process data in smaller chunks rather than loading everything at once.",
            "Use generators and lazy evaluation to reduce peak memory usage.",
            "Profile memory with `tracemalloc` or `memory_profiler` to find the hotspot.",
            "Upgrade the execution environment if the workload legitimately requires more RAM.",
        ],
    ),
]


# ---------------------------------------------------------------------------
# Environment / context inference
# ---------------------------------------------------------------------------

_CONTEXT_PATTERNS: list[tuple[str, str]] = [
    (r"flask|werkzeug|@app\.route|Blueprint", "Flask (web backend)"),
    (r"fastapi|uvicorn|@router\.|APIRouter", "FastAPI (web backend)"),
    (r"django|wsgi|settings\.py|migrations", "Django (web backend)"),
    (r"pytest|unittest|TestCase|assert.*==|def test_", "Testing framework"),
    (r"sqlalchemy|psycopg2|pymysql|sqlite3|cursor\.execute", "Database / ORM"),
    (r"pygame|panda3d|godot|bpy\.|blender", "Game / 3D environment"),
    (r"celery|dramatiq|rq\.|task\.delay", "Task queue / worker"),
    (r"boto3|s3:|aws_|lambda_handler", "AWS / cloud"),
    (r"docker|kubernetes|kubectl|helm", "Container / orchestration"),
    (r"pandas|numpy|sklearn|torch|tensorflow|keras", "Data science / ML"),
]


# ---------------------------------------------------------------------------
# Stack trace parser
# ---------------------------------------------------------------------------

_FRAME_RE = re.compile(
    r'File "([^"]+)", line (\d+), in (\S+)\s*\n\s*(.+)?'
)


def _parse_frames(text: str) -> list[StackFrame]:
    frames: list[StackFrame] = []
    for m in _FRAME_RE.finditer(text):
        frames.append(
            StackFrame(
                file=m.group(1),
                line=int(m.group(2)),
                function=m.group(3),
                source=m.group(4).strip() if m.group(4) else "",
            )
        )
    return frames


# ---------------------------------------------------------------------------
# Context inference
# ---------------------------------------------------------------------------

def _infer_context(text: str) -> str:
    for pattern, label in _CONTEXT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return "General Python"


# ---------------------------------------------------------------------------
# Core analyser
# ---------------------------------------------------------------------------

def analyze(text: str) -> list[DiagnosticResult]:
    """
    Analyse *text* (a log, traceback, or error dump) and return a list of
    :class:`DiagnosticResult` objects, one per detected error.
    """
    results: list[DiagnosticResult] = []
    frames = _parse_frames(text)
    context = _infer_context(text)

    for pattern, error_type, base_confidence, explanation_tpl, fixes_tpl in _ERROR_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            match_val = m.group(1) if m.lastindex and m.lastindex >= 1 else ""
            match2_val = m.group(2) if m.lastindex and m.lastindex >= 2 else ""

            explanation = explanation_tpl.replace("{match}", match_val).replace(
                "{match2}", match2_val
            )
            fixes = [
                f.replace("{match}", match_val).replace("{match2}", match2_val)
                for f in fixes_tpl
            ]

            # Slight confidence bump when stack frames are present
            confidence = min(base_confidence + (0.02 if frames else 0.0), 1.0)

            # Raw excerpt: grab ~3 lines around the match
            start = max(0, m.start() - 120)
            end = min(len(text), m.end() + 120)
            excerpt = text[start:end].strip()

            results.append(
                DiagnosticResult(
                    error_type=error_type,
                    message=m.group(0),
                    confidence=confidence,
                    explanation=explanation,
                    fixes=fixes,
                    context=context,
                    frames=frames,
                    raw_excerpt=excerpt,
                )
            )
            break  # one match per pattern is enough

    return results
