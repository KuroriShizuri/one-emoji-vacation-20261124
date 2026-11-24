"""One-emoji dream vacation entry for make.fun.

Writes the single emoji standing in for our dream vacation to entry.txt
in the output directory ($MAKEFUN_OUTPUT_DIR, default /output). Stdlib
only, deterministic.

The entry (1 character):

    🌌

Why it works: the northern lights are the trip itself — a sky on fire
over snow, the one postcard no beach can send. It is vivid at a glance
(a stranger sees the place before reading a word), personal and
specific (not "a holiday", but the aurora: Iceland, a cold dark sky,
one bucket-list night), fresh against the obvious island cliché, and
readable instantly on any screen at any size. A dream vacation is not
where you lie down; it is the one night you would cross the world for.

Gate (from the competition rules): /output/entry.txt must be UTF-8 text
of 1 to 8 characters, not only white space. The entry is written with
no trailing newline so the file holds exactly the judged emoji.

Validation is stricter than the gate on purpose: the entry must be
exactly one emoji — a single code point in the emoji ranges, with no
whitespace, no variation selector, no zero-width joiner, no skin-tone
modifier and no other character — so a typo in the entry is caught
here instead of reaching the judge.

Usage:
    python3 main.py                  write entry.txt (default output dir)
    python3 main.py --out DIR        write entry.txt under DIR
    python3 main.py --check          validate ENTRY only, write nothing
    python3 main.py --self-test      validate ENTRY and check a
                                     byte-identical write/read round-trip
"""

import argparse
import os
import sys
import tempfile
import unicodedata

ENTRY = "\U0001f30c"  # 🌌 MILKY WAY

MAX_CHARS = 8

# Code-point ranges that count as emoji for this entry (single emoji,
# no modifiers, no joiners). U+1F30C MILKY WAY sits in the
# Miscellaneous Symbols and Pictographs block.
EMOJI_RANGES = (
    (0x1F000, 0x1FAFF),  # emoticons, pictographs, transport, etc.
    (0x2600, 0x27BF),    # misc symbols and dingbats
    (0x2B00, 0x2BFF),    # misc symbols and arrows
    (0xFE00, 0xFE0F),    # variation selectors (rejected, listed for clarity)
    (0x200D, 0x200D),    # zero-width joiner (rejected)
)


def _is_emoji(cp: int) -> bool:
    """True when code point `cp` is an emoji character (not a modifier)."""
    if cp in (0xFE0F, 0x200D):
        return False
    if 0x1F3FB <= cp <= 0x1F3FF:  # skin-tone modifiers
        return False
    return any(lo <= cp <= hi for lo, hi in EMOJI_RANGES)


def validate(text: str) -> list[str]:
    """Return a list of gate failures for `text` (empty means valid).

    Checks, in order: exactly one character, that character is an
    emoji, no whitespace, and UTF-8 encodability. Every failure is
    reported at once so a bad edit shows the full picture instead of
    one error at a time.
    """
    problems = []
    if len(text) != 1:
        problems.append(
            f"length {len(text)} chars, must be exactly 1 emoji"
        )
    if len(text) > MAX_CHARS:
        problems.append(f"length {len(text)} chars, gate allows 1-{MAX_CHARS}")
    if text and not _is_emoji(ord(text[0])):
        problems.append(
            f"character U+{ord(text[0]):04X} ({unicodedata.name(text[0], '?')}) "
            "is not an emoji"
        )
    if any(ch.isspace() for ch in text):
        problems.append("entry contains whitespace (must be exactly one emoji)")
    if text != text.strip():
        problems.append("entry has leading or trailing whitespace")
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:  # pragma: no cover - defensive
        problems.append(f"not encodable as UTF-8: {exc}")
    return problems


def write_entry(out_dir: str) -> str:
    """Write ENTRY to entry.txt under `out_dir`; return the file path."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.txt")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(ENTRY)
    return path


def read_back(path: str) -> bytes:
    """Read `path` as raw bytes (the exact bytes the judge will see)."""
    with open(path, "rb") as f:
        return f.read()


def self_test() -> int:
    """Validate ENTRY, write it to a temp dir, read it back, compare bytes.

    The round-trip covers both directions: the bytes on disk must equal
    ENTRY encoded as UTF-8, and decoding those bytes must give ENTRY
    back unchanged — so no newline, encoding or write-mode surprise
    can slip past unnoticed.
    """
    problems = validate(ENTRY)
    if problems:
        print("self-test FAIL: " + "; ".join(problems), file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        path = write_entry(tmp)
        raw = read_back(path)
        if raw != ENTRY.encode("utf-8"):
            print("self-test FAIL: read-back bytes differ from ENTRY",
                  file=sys.stderr)
            return 1
        if raw.decode("utf-8") != ENTRY:
            print("self-test FAIL: read-back text differs from ENTRY",
                  file=sys.stderr)
            return 1
    print(f"self-test OK: {ENTRY} (U+{ord(ENTRY):04X}), 1 emoji, "
          f"byte-identical round-trip")
    return 0


def check_entry() -> int:
    """Validate ENTRY and report the result; write no file."""
    problems = validate(ENTRY)
    if problems:
        print("check FAIL: " + "; ".join(problems), file=sys.stderr)
        return 1
    print(f"check OK: {ENTRY} (U+{ord(ENTRY):04X}), exactly one emoji, "
          f"no whitespace")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None,
                        help="output directory (default: "
                             "$MAKEFUN_OUTPUT_DIR or /output)")
    parser.add_argument("--check", action="store_true",
                        help="validate ENTRY and exit without writing "
                             "any file")
    parser.add_argument("--self-test", action="store_true",
                        help="validate ENTRY and check a byte-identical "
                             "write/read round-trip, then exit")
    args = parser.parse_args(argv)

    if args.check:
        return check_entry()

    if args.self_test:
        return self_test()

    problems = validate(ENTRY)
    if problems:
        print("invalid ENTRY: " + "; ".join(problems), file=sys.stderr)
        return 1

    out_dir = args.out or os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    path = write_entry(out_dir)
    # Read back and confirm the file holds exactly the entry.
    if read_back(path) != ENTRY.encode("utf-8"):
        print(f"read-back mismatch in {path}", file=sys.stderr)
        return 1
    print(f"wrote {path} ({ENTRY}, 1 emoji)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
