#!/usr/bin/env python3
"""Write a styled static HTML report for one byte. Standard library only."""
from html import escape
from pathlib import Path

# ---- Input (edit here) -----------------------------------------------------
BYTE_HEX = "1C"
OUTPUT = "byte_report.html"

DATETIME = "2026-11-15 10:30:00"
MODEL1_NUMBER = "MODEL1-0001"
MODEL2_NUMBER = "MODEL2-0001"

# Lines shown at the top of the report, in order: (label, value).
# Add more (label, value) pairs here to get more lines.
INFO_LINES = [
    ("Datetime", DATETIME),
    ("Model1 number", MODEL1_NUMBER),
    ("Model2 number", MODEL2_NUMBER),
]

# name, highest bit, lowest bit, optional {value: meaning}
FIELDS = [
    ("Flag 7", 7, 7, {}),
    ("Combination (bits 6-4)", 6, 4, {}),   # e.g. {1: "Init", 2: "Run"}
    ("Flag 3", 3, 3, {}),
    ("Flag 2", 2, 2, {}),
    ("Flag 1", 1, 1, {}),
    ("Flag 0", 0, 0, {}),
]
# ----------------------------------------------------------------------------

value = int(BYTE_HEX, 16)
if not 0 <= value <= 0xFF:
    raise SystemExit("Value must fit in one byte (00..FF)")
binary = f"{value:08b}"

# ---- Decode fields ----------------------------------------------------------
decoded, multi_bits = [], set()
for name, hi, lo, meanings in FIELDS:
    width = hi - lo + 1
    v = (value >> lo) & ((1 << width) - 1)
    if width == 1:
        kind, result = ("set", "set") if v else ("clear", "clear")
    else:
        kind = "value"
        result = f"{v} ({meanings[v]})" if v in meanings else str(v)
        multi_bits.update(range(lo, hi + 1))
    decoded.append(dict(name=name, hi=hi, lo=lo, width=width, v=v, kind=kind,
                        result=result, bits=str(hi) if width == 1 else f"{hi}..{lo}",
                        binary=f"{v:0{width}b}"))

# ---- Build HTML pieces ------------------------------------------------------
meta = "".join(
    f"<div class='meta'><span>{escape(l)}</span><b>{escape(str(v))}</b></div>"
    for l, v in INFO_LINES
)

strip = []
for i in range(7, -1, -1):
    col, bit = 8 - i, (value >> i) & 1
    cls = "cell" + (" one" if bit else "") + (" grp" if i in multi_bits else "")
    strip.append(f"<div class='idx' style='grid-area:1/{col}'>bit {i}</div>")
    strip.append(f"<div class='{cls}' style='grid-area:2/{col}'>{bit}</div>")
for d in decoded:
    cls = "bar " + d["kind"]
    strip.append(
        f"<div class='{cls}' style='grid-area:3/{8 - d['hi']}/auto/span {d['width']}'>"
        f"<b>{escape(d['name'])}</b><span>{escape(d['result'])}</span></div>"
    )

rows = "\n".join(
    f"<tr><td>{escape(d['name'])}</td><td class='m'>{d['bits']}</td>"
    f"<td class='m'>{d['binary']}</td>"
    f"<td><span class='pill {d['kind']}'>{escape(d['result'])}</span></td></tr>"
    for d in decoded
)
set_count = sum(1 for d in decoded if d["kind"] == "set")
flag_count = sum(1 for d in decoded if d["width"] == 1)

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Byte report __HEX__</title>
<style>
:root{
  --paper:#e9eef3; --card:#ffffff; --ink:#16233b; --muted:#5b6a82; --line:#d0d9e3;
  --hero:#14213d; --hero-ink:#f2f5fa; --hero-muted:#9fb0c9;
  --set:#0d7a68; --set-bg:#d9f1ec; --grp:#4a3fc7; --grp-bg:#e8e6fb; --clear-bg:#e9eef3;
}
@media (prefers-color-scheme: dark){
  :root{--paper:#10161f; --card:#1a2331; --ink:#e4eaf3; --muted:#93a1b8; --line:#2f3b4f;
    --hero:#0b1220; --set:#3cc5ac; --set-bg:#133a35; --grp:#a29cff; --grp-bg:#2b2a52; --clear-bg:#232d3d;}
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font:16px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
.mono,.m,h1,.bin{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.page{max-width:860px;margin:0 auto;padding:clamp(12px,3vw,36px)}

.hero{background:var(--hero);color:var(--hero-ink);border-radius:16px;
  padding:clamp(20px,4vw,36px);display:flex;flex-wrap:wrap;gap:20px 40px;
  align-items:flex-end;justify-content:space-between;
  background-image:repeating-linear-gradient(135deg,rgba(255,255,255,.035) 0 2px,transparent 2px 14px)}
.hero small{display:block;color:var(--hero-muted);font-size:14px;margin-bottom:2px}
h1{margin:0;font-size:clamp(48px,12vw,88px);line-height:1;letter-spacing:-.03em;font-weight:700}
.facts{display:flex;gap:28px}
.facts div b{display:block;font-size:clamp(20px,4vw,28px);font-weight:600}
.bin{letter-spacing:.06em}

.metas{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:14px 0 0}
.meta{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--grp);
  border-radius:10px;padding:10px 14px}
.meta span{display:block;font-size:13px;color:var(--muted)}
.meta b{font-family:ui-monospace,Menlo,Consolas,monospace;font-weight:600;word-break:break-all}

section{background:var(--card);border:1px solid var(--line);border-radius:16px;
  padding:clamp(16px,3vw,28px);margin-top:18px}
h2{margin:0 0 16px;font-size:18px}
h2 em{font-style:normal;color:var(--muted);font-weight:400;font-size:14px;margin-left:8px}

.strip{display:grid;grid-template-columns:repeat(8,1fr);gap:6px}
.idx{text-align:center;font-size:12px;color:var(--muted)}
.cell{aspect-ratio:1;display:grid;place-items:center;border-radius:10px;
  border:2px solid var(--line);background:var(--clear-bg);color:var(--muted);
  font:700 clamp(20px,5.5vw,36px) ui-monospace,Menlo,Consolas,monospace}
.cell.one{background:var(--set);border-color:var(--set);color:#fff}
.cell.grp{border-color:var(--grp);background:var(--grp-bg);color:var(--grp)}
.cell.grp.one{background:var(--grp);color:#fff}
.bar{margin-top:2px;border-radius:10px;padding:8px 6px;text-align:center;font-size:13px;
  line-height:1.25;display:flex;flex-direction:column;justify-content:center;
  border:2px solid var(--line);background:var(--clear-bg)}
.bar b{font-weight:600}
.bar.set{background:var(--set-bg);border-color:var(--set)}
.bar.value{background:var(--grp-bg);border-color:var(--grp)}
.bar span{color:var(--muted)}

table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:10px 8px;border-bottom:1px solid var(--line);font-size:15px}
th{color:var(--muted);font-weight:500;font-size:13px}
tr:last-child td{border-bottom:0}
.pill{display:inline-block;padding:2px 12px;border-radius:999px;font-size:13px;font-weight:600;
  font-family:ui-monospace,Menlo,Consolas,monospace}
.pill.set{background:var(--set-bg);color:var(--set)}
.pill.clear{background:var(--clear-bg);color:var(--muted)}
.pill.value{background:var(--grp-bg);color:var(--grp)}
.legend{display:flex;gap:16px;flex-wrap:wrap;margin-top:16px;font-size:13px;color:var(--muted)}
.legend i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px}
@media print{body{background:#fff}.hero{background-image:none}}
</style>
</head>
<body>
<div class="page">
  <header class="hero">
    <div><small>Byte report</small><h1>__HEX__</h1></div>
    <div class="facts">
      <div><small>Decimal</small><b class="mono">__DEC__</b></div>
      <div><small>Binary</small><b class="bin">__BIN__</b></div>
      <div><small>Bits set</small><b class="mono">__ONES__ / 8</b></div>
    </div>
  </header>

  <div class="metas">__META__</div>

  <section>
    <h2>Bit layout<em>bit 7 is the leftmost bit</em></h2>
    <div class="strip">__STRIP__</div>
    <div class="legend">
      <span><i style="background:var(--set)"></i>flag set</span>
      <span><i style="background:var(--clear-bg);border:1px solid var(--line)"></i>flag clear</span>
      <span><i style="background:var(--grp)"></i>multi-bit field</span>
    </div>
  </section>

  <section>
    <h2>Decoded fields<em>__SETFLAGS__ of __FLAGS__ flags set</em></h2>
    <table>
      <tr><th>Field</th><th>Bits</th><th>Binary</th><th>Value</th></tr>
      __ROWS__
    </table>
  </section>
</div>
</body>
</html>
"""

html = (TEMPLATE
        .replace("__HEX__", f"0x{value:02X}")
        .replace("__DEC__", str(value))
        .replace("__BIN__", f"{binary[:4]} {binary[4:]}")
        .replace("__ONES__", str(binary.count("1")))
        .replace("__META__", meta)
        .replace("__STRIP__", "\n".join(strip))
        .replace("__SETFLAGS__", str(set_count))
        .replace("__FLAGS__", str(flag_count))
        .replace("__ROWS__", rows))

Path(OUTPUT).write_text(html, encoding="utf-8")
print(f"Wrote {Path(OUTPUT).resolve()}")
