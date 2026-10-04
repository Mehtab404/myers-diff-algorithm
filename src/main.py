"""Myers' O(ND) diff: line diff (Part A) and changed-character ranges (Part B).

The diff core works on any sequence of hashable items, so the same code
diffs lines (bytes) for Part A and characters (str) for Part B.
"""
import sys


def read_lines(path):
    """Read a file as raw bytes and split it into lines (brief, Section 2)."""
    with open(path, "rb") as f:
        data = f.read()
    lines = data.split(b"\n")
    if lines[-1] == b"":
        lines.pop()  # a final newline makes no extra empty line
    return lines


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[1] not in ("lines", "highlight"):
        print("usage: main.py lines|highlight A_PATH B_PATH", file=sys.stderr)
        return 2
    command, a_path, b_path = sys.argv[1:]
    try:
        a = read_lines(a_path)
        b = read_lines(b_path)
    except OSError as e:
        print("error: cannot read file: %s" % e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
