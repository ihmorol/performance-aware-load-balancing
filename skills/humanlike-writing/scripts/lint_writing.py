#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


PROHIBITED = re.compile(
    r"\b(?:delv(?:e|es|ed|ing)|moreover|furthermore|"
    r"underscor(?:e|es|ed|ing))\b", re.IGNORECASE
)
STOCK = re.compile(
    r"\b(?:additionally|utilize|leverag\w*|synerg\w*|tapestry|"
    r"pivotal|seamless\w*|transformative|robust)\b", re.IGNORECASE
)
RESIDUE = re.compile(
    r"\b(?:great question|i hope this helps|let me know if you need|"
    r"as an ai language model|here is (?:your|the) rewritten|"
    r"let me think step by step|in conclusion)\b", re.IGNORECASE
)


def mask_protected(text):
    lines = text.splitlines(keepends=True)
    masked = []
    fence_char = None
    fence_size = 0
    for line in lines:
        fence = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        protect = fence_char is not None
        if fence_char is not None and fence:
            marker, rest = fence.groups()
            if marker[0] == fence_char and len(marker) >= fence_size and not rest.strip():
                fence_char = None
        elif fence_char is None and fence:
            marker, _ = fence.groups()
            fence_char = marker[0]
            fence_size = len(marker)
            protect = True
        if re.match(r"^\s*>", line):
            protect = True
        masked.append(re.sub(r"[^\r\n]", " ", line) if protect else line)
    prose = "".join(masked)
    protected_patterns = [
        r"(`+)([^`\n]*?)\1",
        r'"(?:[^"\\\n]|\\.)*"',
        r"\u201c[^\u201d\n]*\u201d",
        r"\b[a-zA-Z][a-zA-Z0-9+.-]*://[^\s<>]+",
        r"\]\([^\n)]*\)",
        r"\([^()\n]*\b(?:19|20)\d{2}[a-z]?[^()\n]*\)",
    ]
    for pattern in protected_patterns:
        prose = re.sub(pattern, lambda m: " " * len(m.group()), prose)
    return prose


def findings(text, protected_literals=()):
    prose = mask_protected(text)
    for literal in protected_literals:
        if literal:
            prose = prose.replace(literal, " " * len(literal))
    flags = []

    def add(code, severity, start, excerpt, reason):
        flags.append({"code": code, "severity": severity,
                      "line": text.count("\n", 0, start) + 1,
                      "excerpt": excerpt, "reason": reason})

    for match in PROHIBITED.finditer(prose):
        add("prohibited-word", "error", match.start(), match.group(),
            "Replace in authored prose; manually exempt exact quoted/technical content.")
    for match in re.finditer("\u2014", prose):
        add("em-dash", "error", match.start(), match.group(),
            "The user's prose preference bans em dashes; preserve protected material.")
    for pattern, code, reason in [
        (STOCK, "stock-vocabulary", "Review meaning and technical context before replacing."),
        (RESIDUE, "chatbot-residue", "Remove only when it is residue rather than requested content."),
    ]:
        for match in pattern.finditer(prose):
            add(code, "warning", match.start(), match.group(), reason)

    sentences = []
    for match in re.finditer(r"[^.!?\n]+[.!?]?", prose):
        words = re.findall(r"\b[\w]+(?:['\u2019][\w]+)?\b", match.group())
        if words:
            sentences.append((match.start(), match.group().strip(), words))
    for index in range(len(sentences) - 2):
        run = sentences[index:index + 3]
        lengths = [len(item[2]) for item in run]
        if max(lengths) - min(lengths) <= 3:
            add("similar-length-run", "warning", run[0][0],
                " / ".join(str(n) for n in lengths),
                "Review this three-sentence rhythm; do not pad or alter facts for variation.")
        openers = [item[2][0].lower() for item in run]
        if len(set(openers)) == 1:
            add("repeated-opener", "warning", run[0][0], openers[0],
                "Review accidental repetition; deliberate anaphora can be appropriate.")
    errors = sum(flag["severity"] == "error" for flag in flags)
    return {"authorship_assessment": None, "errors": errors,
            "warnings": len(flags) - errors, "findings": flags,
            "limitations": "Not an AI detector, fact checker, citation verifier, or complete style audit."}


def main():
    parser = argparse.ArgumentParser(description="Check prose conventions; never assess authorship.")
    parser.add_argument("path", nargs="?", help="UTF-8 draft; omit to read stdin")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable report")
    parser.add_argument("--protect", action="append", default=[],
                        help="Exclude an exact source-grounded name or technical span; repeat as needed")
    args = parser.parse_args()
    try:
        text = Path(args.path).read_text(encoding="utf-8") if args.path else sys.stdin.read()
    except (OSError, UnicodeError) as error:
        parser.exit(2, f"Cannot read draft: {error}\n")
    report = findings(text, args.protect)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Prose flags: {report['errors']} errors, {report['warnings']} warnings")
        for flag in report["findings"]:
            print(f"{flag['severity']} line {flag['line']} {flag['code']}: {flag['excerpt']}")
        print(report["limitations"])
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
