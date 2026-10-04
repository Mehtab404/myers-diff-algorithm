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


def middle_snake(A, B, Ar, Br, n, m):
    """Find the middle snake of the edit graph of A (length n) and B (length m).

    A and B end with one sentinel each (-1 and -2) so a snake can never run
    past the end. Ar and Br are the reversed sequences, also with sentinels.
    Returns (sx, sy, ex, ey): the snake runs from (sx, sy) to (ex, ey). The
    problem splits into (0,0)-(sx,sy) and (ex,ey)-(n,m).
    """
    delta = n - m
    odd = delta & 1
    max_d = (n + m + 1) // 2
    off = max_d + 1
    size = 2 * max_d + 3
    # vf[off+k]: furthest x on diagonal k = x - y going forward from (0, 0).
    # vb[off+k]: the same, going backward from (n, m) in reversed coordinates.
    # -1 means "diagonal not reached yet".
    vf = [-1] * size
    vb = [-1] * size
    vf[off + 1] = 0
    vb[off + 1] = 0
    # A diagonal that runs off the right or bottom edge of the grid is dropped
    # from the search range: fs/fe (forward) and bs/be (backward).
    fs = fe = bs = be = 0
    for d in range(max_d + 1):
        # ---- forward paths with d edits ----
        for k in range(-d + fs, d - fe + 1, 2):
            i = off + k
            if k == -d or (k != d and vf[i - 1] < vf[i + 1]):
                x = vf[i + 1]  # step down: insertion
            else:
                x = vf[i - 1] + 1  # step right: deletion
            y = x - k
            x0 = x
            y0 = y
            if x <= n and y <= m:
                while A[x] == B[y]:  # follow the snake
                    x += 1
                    y += 1
            vf[i] = x
            if x > n:
                fe += 2
            elif y > m:
                fs += 2
            elif odd:
                kr = delta - k
                if -d < kr < d:  # backward diagonal computed in step d-1
                    xb = vb[off + kr]
                    if xb != -1 and x + xb >= n:
                        return x0, y0, x, y
        # ---- backward paths with d edits ----
        for k in range(-d + bs, d - be + 1, 2):
            i = off + k
            if k == -d or (k != d and vb[i - 1] < vb[i + 1]):
                x = vb[i + 1]
            else:
                x = vb[i - 1] + 1
            y = x - k
            x0 = x
            y0 = y
            if x <= n and y <= m:
                while Ar[x] == Br[y]:
                    x += 1
                    y += 1
            vb[i] = x
            if x > n:
                be += 2
            elif y > m:
                bs += 2
            elif not odd:
                kf = delta - k
                if -d <= kf <= d:  # forward diagonal computed in step d
                    xf = vf[off + kf]
                    if xf != -1 and xf + x >= n:
                        return n - x, m - y, n - x0, m - y0
    raise RuntimeError("middle snake not found")


def diff_marks(a, b):
    """Minimal diff of two sequences.

    Returns (del_a, ins_b): bytearrays with 1 at every element of a that is
    deleted and every element of b that is inserted. The elements marked 0
    are matched to each other in order.
    """
    na = len(a)
    nb = len(b)
    # Give every distinct item a small integer so comparisons are cheap.
    ids = {}
    ia = [ids.setdefault(x, len(ids)) for x in a]
    ib = [ids.setdefault(x, len(ids)) for x in b]
    # An item that occurs in only one sequence can never be matched, so it is
    # always deleted/inserted. Dropping it keeps the diff minimal and makes
    # the search smaller.
    in_a = set(ia)
    in_b = set(ib)
    ma = [i for i, v in enumerate(ia) if v in in_b]
    mb = [j for j, v in enumerate(ib) if v in in_a]
    fa = [ia[i] for i in ma]
    fb = [ib[j] for j in mb]

    del_f = bytearray(len(fa))
    ins_f = bytearray(len(fb))
    stack = [(0, len(fa), 0, len(fb))]
    while stack:
        a0, a1, b0, b1 = stack.pop()
        # Common prefix and suffix are always part of some minimal diff.
        while a0 < a1 and b0 < b1 and fa[a0] == fb[b0]:
            a0 += 1
            b0 += 1
        while a0 < a1 and b0 < b1 and fa[a1 - 1] == fb[b1 - 1]:
            a1 -= 1
            b1 -= 1
        if a0 == a1:
            if b0 < b1:
                ins_f[b0:b1] = b"\x01" * (b1 - b0)
            continue
        if b0 == b1:
            del_f[a0:a1] = b"\x01" * (a1 - a0)
            continue
        A = fa[a0:a1]
        B = fb[b0:b1]
        n = a1 - a0
        m = b1 - b0
        Ar = A[::-1]
        Br = B[::-1]
        A.append(-1)
        B.append(-2)
        Ar.append(-1)
        Br.append(-2)
        sx, sy, ex, ey = middle_snake(A, B, Ar, Br, n, m)
        stack.append((a0, a0 + sx, b0, b0 + sy))
        stack.append((a0 + ex, a1, b0 + ey, b1))

    # Map the marks back to the full sequences.
    del_a = bytearray(b"\x01") * na
    ins_b = bytearray(b"\x01") * nb
    for idx, i in enumerate(ma):
        del_a[i] = del_f[idx]
    for idx, j in enumerate(mb):
        ins_b[j] = ins_f[idx]
    return del_a, ins_b


def ranges(marks):
    """Turn a 0/1 bytearray into 'start-end,start-end' (or '.' if no 1s)."""
    n = len(marks)
    parts = []
    p = marks.find(1)
    while p != -1:
        q = marks.find(0, p)
        if q == -1:
            q = n
        parts.append("%d-%d" % (p, q))
        p = marks.find(1, q) if q < n else -1
    return ",".join(parts) if parts else "."


def build_output(a, b, del_a, ins_b, highlight):
    """Walk the edit script and build the output lines (deletes before inserts)."""
    na = len(a)
    nb = len(b)
    out = []
    i = j = 0
    while True:
        nd = del_a.find(1, i)
        ni = ins_b.find(1, j)
        if nd == -1 and ni == -1:
            break
        # keep lines until the next change
        c = na - i
        if nd != -1:
            c = min(c, nd - i)
        if ni != -1:
            c = min(c, ni - j)
        if c:
            out.extend([b" " + line for line in a[i:i + c]])
            i += c
            j += c
        # one change block: a run of deletes, then a run of inserts
        i2 = del_a.find(0, i)
        if i2 == -1:
            i2 = na
        j2 = ins_b.find(0, j)
        if j2 == -1:
            j2 = nb
        dels = a[i:i2]
        inss = b[j:j2]
        out.extend([b"-" + line for line in dels])
        if not highlight:
            out.extend([b"+" + line for line in inss])
        else:
            paired = min(len(dels), len(inss))
            for t in range(len(inss)):
                out.append(b"+" + inss[t])
                if t < paired:
                    old = dels[t].decode("utf-8", "surrogateescape")
                    new = inss[t].decode("utf-8", "surrogateescape")
                    dm, im = diff_marks(old, new)
                    out.append(("? %s | %s" % (ranges(dm), ranges(im))).encode("utf-8"))
        i = i2
        j = j2
    if i < na:
        out.extend([b" " + line for line in a[i:]])
    return out


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
    del_a, ins_b = diff_marks(a, b)
    out = build_output(a, b, del_a, ins_b, command == "highlight")
    if out:
        sys.stdout.buffer.write(b"\n".join(out) + b"\n")
        sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
