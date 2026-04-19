"""
cli.py — Command-line interface for Bug Autopsy.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from autopsy.analyzer import analyze, DiagnosticResult
from autopsy import report as report_mod


# ---------------------------------------------------------------------------
# Console rendering
# ---------------------------------------------------------------------------

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
DIM    = "\033[2m"


def _supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(text: str, *codes: str) -> str:
    if not _supports_color():
        return text
    return "".join(codes) + text + RESET


def _confidence_color(score: float) -> str:
    if score >= 0.90:
        return RED
    if score >= 0.70:
        return YELLOW
    return GREEN


def _bar(score: float, width: int = 20) -> str:
    filled = round(score * width)
    return "[" + "█" * filled + "░" * (width - filled) + f"] {score:.0%}"


def _print_header(n: int) -> None:
    print()
    print(_c("╔══════════════════════════════════════════╗", CYAN, BOLD))
    print(_c("║         🔬  B U G   A U T O P S Y       ║", CYAN, BOLD))
    print(_c("╚══════════════════════════════════════════╝", CYAN, BOLD))
    print(_c(f"  {n} error(s) detected\n", DIM))


def _print_result(idx: int, r: DiagnosticResult) -> None:
    cc = _confidence_color(r.confidence)

    print(_c(f"┌─ [{idx}] {r.error_type}", cc, BOLD))
    print(_c(f"│  Message  : {r.message}", DIM))
    print(_c(f"│  Context  : {r.context}", DIM))
    print(
        _c("│  Confidence: ", DIM)
        + _c(_bar(r.confidence), cc)
    )
    print(_c("│", DIM))
    print(_c("│  🧠 Explanation", BOLD))
    for line in r.explanation.splitlines():
        print(f"│     {line}")
    print(_c("│", DIM))

    if r.frames:
        print(_c("│  📍 Stack Trace Locations", BOLD))
        for frame in r.frames[-3:]:   # show last 3 frames
            print(f"│     • {frame.function}()  →  {frame.file}:{frame.line}")
            if frame.source:
                print(_c(f"│       {frame.source}", DIM))
        print(_c("│", DIM))

    print(_c("│  🔧 Recommended Fixes", BOLD))
    for i, fix in enumerate(r.fixes, 1):
        print(f"│   {i}. {fix}")

    print(_c("└" + "─" * 60, cc))
    print()


def _print_no_errors() -> None:
    print()
    print(_c("✅  No known error patterns detected.", GREEN, BOLD))
    print(_c("    This does not guarantee the input is error-free.", DIM))
    print()


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def _read_input(args: argparse.Namespace) -> tuple[str, str]:
    """Return (text, source_label)."""
    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(_c(f"Error: file not found — {args.file}", RED, BOLD), file=sys.stderr)
            sys.exit(1)
        return path.read_text(encoding="utf-8", errors="replace"), str(path)

    if args.text:
        return args.text, "stdin (--text)"

    # Read from stdin if neither flag was provided
    if not sys.stdin.isatty():
        return sys.stdin.read(), "stdin (pipe)"

    print(
        _c("No input provided. Use --file <path> or --text '<content>'.", RED),
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="autopsy",
        description="🔬 Bug Autopsy — turn raw tracebacks into actionable insights.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  autopsy --file error.log
  autopsy --text "NameError: name 'db' is not defined"
  cat traceback.txt | autopsy
  autopsy --file crash.log --report report.md
        """,
    )
    parser.add_argument("--file", "-f", metavar="PATH", help="Path to a log / traceback file")
    parser.add_argument("--text", "-t", metavar="TEXT", help="Inline log / error text")
    parser.add_argument(
        "--report", "-r", metavar="PATH",
        help="Save a Markdown autopsy report to this path (e.g. report.md)"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Suppress console output (useful when only a report is needed)"
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="Disable ANSI colour output"
    )

    args = parser.parse_args(argv)

    if args.no_color:
        # Monkey-patch colour off
        global _supports_color
        _supports_color = lambda: False  # noqa: E731

    text, source_label = _read_input(args)
    results = analyze(text)

    # ── Console output ────────────────────────────────────────────────────
    if not args.quiet:
        _print_header(len(results))
        if results:
            for i, r in enumerate(results, 1):
                _print_result(i, r)
        else:
            _print_no_errors()

    # ── Optional Markdown report ──────────────────────────────────────────
    if args.report:
        md = report_mod.generate(results, source_label=source_label)
        report_mod.save(md, args.report)

    return 0 if results else 0


def entry_point() -> None:
    sys.exit(main())


if __name__ == "__main__":
    entry_point()
