"""Write SRT captions from the CAPTIONS table in src/data.ts (plus the end-card line).

Usage: python make_srt.py <src/data.ts> <out.srt>
"""
import re, sys

src, out = sys.argv[1], sys.argv[2]
body = open(src, encoding="utf-8").read()
body = body[body.index("export const CAPTIONS"):]
rows = []
for m in re.finditer(r"\{ start: ([\d.]+), end: ([\d.]+),[^\n]*?words: \[(.*?)\] \}", body):
    words = re.findall(r'w: "([^"]+)"', m.group(3))
    rows.append((float(m.group(1)), float(m.group(2)), " ".join(words)))
rows.append((37.38, 38.9, "Shuruaat… isi video se."))

def ts(x):
    ms = int(round(x * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

with open(out, "w", encoding="utf-8") as fh:
    for i, (a, b, line) in enumerate(rows, 1):
        fh.write(f"{i}\n{ts(a)} --> {ts(b)}\n{line}\n\n")
print(len(rows), "cues")
