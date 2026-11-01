import json, os, sys, subprocess
src, out = sys.argv[1], sys.argv[2]
items = json.load(open(src))
seen = {}
for it in items:
    name = it['path']
    base, ext = os.path.splitext(name)
    seen[name] = seen.get(name, 0) + 1
    if seen[name] > 1:
        name = f"{base}_{seen[name]}{ext}"
    dest = os.path.join(out, name)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print("skip", name, flush=True); continue
    fid = it['url'].split('id=')[1]
    r = subprocess.run(['gdown', '-q', fid, '-O', dest])
    print(("ok " if r.returncode == 0 else "FAIL ") + name, os.path.getsize(dest) if os.path.exists(dest) else 0, flush=True)
print("ALL DONE", flush=True)
