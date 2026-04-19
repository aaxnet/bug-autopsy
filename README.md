<div align="center">

```
██████╗ ██╗   ██╗ ██████╗      █████╗ ██╗   ██╗████████╗ ██████╗ ██████╗ ███████╗██╗   ██╗
██╔══██╗██║   ██║██╔════╝     ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗██╔════╝╚██╗ ██╔╝
██████╔╝██║   ██║██║  ███╗    ███████║██║   ██║   ██║   ██║   ██║██████╔╝███████╗ ╚████╔╝
██╔══██╗██║   ██║██║   ██║    ██╔══██║██║   ██║   ██║   ██║   ██║██╔═══╝ ╚════██║  ╚██╔╝
██████╔╝╚██████╔╝╚██████╔╝    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝██║     ███████║   ██║
╚═════╝  ╚═════╝  ╚═════╝     ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝     ╚══════╝   ╚═╝
```

### Turn raw Python tracebacks into actionable insights — in seconds.

<br/>

[![PyPI](https://img.shields.io/pypi/v/bug-autopsy?style=flat-square&color=black)](https://pypi.org/project/bug-autopsy/)
[![Python](https://img.shields.io/badge/python-3.9+-black?style=flat-square)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-black?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-39%20passed-black?style=flat-square)](#)
[![Zero deps](https://img.shields.io/badge/dependencies-zero-black?style=flat-square)](#)

</div>

---

## The problem

Your CI pipeline just failed. There's a wall of red text in the logs.

You scroll. You squint. You grep. You Google the error. You find a Stack Overflow answer from 2016. Maybe it applies. Maybe it doesn't.

**Bug Autopsy fixes that.**

One command reads any log, traceback, or error dump and returns a structured diagnosis — root cause, confidence score, exact stack location, and 2–4 concrete fixes — in the time it takes to read the first line.

---

## Install

```bash
pip install bug-autopsy
```

> No API keys. No network calls. No mandatory dependencies. Works on Python 3.9+, Windows / Linux / macOS.

---

## Quickstart

### Analyse a log file

```bash
autopsy --file path/to/error.log
```

### Analyse inline text

```bash
autopsy --text "ModuleNotFoundError: No module named 'requests'"
```

### Pipe directly from your program

```bash
python my_script.py 2>&1 | autopsy
```

### Generate a Markdown report

```bash
autopsy --file crash.log --report autopsy_report.md
```

---

## Output

```
╔══════════════════════════════════════════╗
║         🔬  B U G   A U T O P S Y       ║
╚══════════════════════════════════════════╝
  2 error(s) detected

┌─ [1] KeyError
│  Message  : KeyError: 'url'
│  Context  : Database / ORM
│  Confidence: [███████████████████░] 95%
│
│  🧠 Explanation
│     The key 'url' was not found in the dictionary. The data
│     structure does not contain this key at the time of access.
│
│  📍 Stack Trace Locations
│     • startup()  →  /srv/api/main.py:47
│       db_url = config['database']['url']
│     • fallback_connect()  →  /srv/api/db.py:18
│
│  🔧 Recommended Fixes
│   1. Use `.get()` with a default: `value = d.get('url', default_value)`
│   2. Check for typos — keys are case-sensitive.
│   3. Verify the key is populated before access.
│   4. Add a guard: `if 'url' in d:` before accessing.
└────────────────────────────────────────────────────────────
```

`autopsy --file crash.log --report report.md` saves a full structured Markdown report:

```markdown
# 🔬 Bug Autopsy Report

**Generated:** 2025-01-15 14:32:01
**Source:** `crash.log`
**Errors found:** 2

| # | Error Type | Confidence        | Environment    |
|---|-----------|-------------------|----------------|
| 1 | KeyError  | [██████████] 95%  | Database / ORM |
| 2 | TypeError | [█████████░] 92%  | Database / ORM |

## Error 1: `KeyError`
...
```

---

## Commands

| Command | Description |
|---|---|
| `autopsy --file <path>` | Analyse a log or traceback file |
| `autopsy --text "<content>"` | Analyse inline error text |
| `cat log.txt \| autopsy` | Pipe from any command |
| `autopsy --file <path> --report out.md` | Save a Markdown report |
| `autopsy --file <path> --quiet` | Suppress console output (report only) |
| `autopsy --no-color` | Disable ANSI colour (CI-friendly) |

---

## Detected error types

| Error Type | What it catches |
|---|---|
| `ModuleNotFoundError` | Missing package or wrong virtual environment |
| `ImportError` | Bad import name, circular import, broken install |
| `KeyError` | Dictionary key not present |
| `IndexError` | List index out of range |
| `TypeError` | Wrong type passed to a function or operation |
| `NameError` | Variable used before assignment |
| `AssertionError` | Failed assertion or broken invariant |
| `PermissionError` | OS file-system permission denied |
| `TimeoutError` | Network or I/O operation timed out |
| `AttributeError` | Attribute not found on an object |
| `ZeroDivisionError` | Division by zero |
| `FileNotFoundError` | File or directory does not exist |
| `RecursionError` | Maximum recursion depth exceeded |
| `UnicodeDecodeError` | Encoding mismatch when reading bytes |
| `ValueError` | Correct type, invalid value |
| `MemoryError` | Out of memory |
| `RuntimeError` | General runtime failure |
| `OSError` | Low-level OS error |
| `StopIteration` | Exhausted iterator used outside generator |

---

## Environment inference

Bug Autopsy automatically detects the environment your error came from and tailors context accordingly.

| Detected environment | Trigger keywords |
|---|---|
| Flask (web backend) | `flask`, `werkzeug`, `Blueprint` |
| FastAPI (web backend) | `fastapi`, `uvicorn`, `APIRouter` |
| Django (web backend) | `django`, `wsgi`, `migrations` |
| Testing framework | `pytest`, `unittest`, `TestCase` |
| Database / ORM | `sqlalchemy`, `psycopg2`, `sqlite3` |
| Data science / ML | `pandas`, `numpy`, `torch`, `sklearn` |
| Task queue / worker | `celery`, `dramatiq`, `rq` |
| AWS / cloud | `boto3`, `lambda_handler` |

---

## Python API

Bug Autopsy can be used programmatically in your own scripts or tools:

```python
from autopsy.analyzer import analyze
from autopsy import report as report_mod

log_text = open("crash.log").read()
results = analyze(log_text)

for r in results:
    print(f"{r.error_type} — {r.confidence:.0%} confidence")
    print(r.explanation)
    for fix in r.fixes:
        print(f"  • {fix}")

# Save a Markdown report
md = report_mod.generate(results, source_label="crash.log")
report_mod.save(md, "autopsy_report.md")
```

Each `DiagnosticResult` contains:

```python
r.error_type    # "KeyError"
r.message       # raw matched line
r.confidence    # 0.0 – 1.0
r.explanation   # human-readable root cause
r.fixes         # list of actionable recommendations
r.context       # inferred environment ("Flask", "pytest", ...)
r.frames        # parsed stack frames (file, line, function, source)
r.raw_excerpt   # surrounding log context
```

---

## Project structure

```
bug-autopsy/
├── autopsy/
│   ├── analyzer.py     # Core parsing, detection & classification
│   ├── cli.py          # Command-line interface
│   └── report.py       # Markdown report generation
├── examples/
│   ├── module_not_found.log
│   ├── multi_error.log
│   ├── flask_error.log
│   └── sample_report.md
├── tests/
│   ├── test_analyzer.py
│   └── test_report.py
├── pyproject.toml
└── README.md
```

---

## Running tests

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# All tests
pytest

# With coverage
pytest --cov=autopsy --cov-report=term-missing
```

All **39 tests** pass on Python 3.9 – 3.12.

---

## Roadmap

- LLM-powered explanations (AI mode)
- GitHub issue analyser
- Auto-reproduction sandbox
- Auto-fix / patch suggestion system
- Web UI dashboard (FastAPI)

---

## Contributing

```bash
git clone https://github.com/yourname/bug-autopsy
cd bug-autopsy
pip install -e ".[dev]"
pytest
```

PRs welcome. See [open issues](https://github.com/yourname/bug-autopsy/issues).

---

<div align="center">
<br/>

If Bug Autopsy saved you a debugging session — a ⭐ helps other developers find it.

<br/>

[![Star on GitHub](https://img.shields.io/badge/Star_on_GitHub-black?style=flat-square&logo=github&logoColor=white)](https://github.com/yourname/bug-autopsy)
[![PyPI](https://img.shields.io/badge/PyPI-black?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/bug-autopsy/)
[![Report a bug](https://img.shields.io/badge/Report_a_bug-black?style=flat-square&logo=github&logoColor=white)](https://github.com/yourname/bug-autopsy/issues/new)

<br/>
</div>
