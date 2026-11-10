import json, os, time, html
D=os.path.dirname(os.path.abspath(__file__))
st=json.load(open(D+"/status.json"))
lab={"todo":"বাকি","doing":"চলছে","done":"হয়েছে"}
done=sum(s["status"]=="done" for s in st["scenes"]); n=len(st["scenes"])
bn=lambda x: str(x).translate(str.maketrans("0123456789","০১২৩৪৫৬৭৮৯"))
ver=int(time.time())
rows=[]
for s in st["scenes"]:
    still=f'stills/s{s["n"]:02d}.jpg'
    img=f'<img src="{still}?v={ver}" alt="সিন {bn(s["n"])} এর ফ্রেম" loading="lazy">' if os.path.exists(D+"/"+still) else '<div class="ph" aria-hidden="true"></div>'
    rows.append(f'''<li class="scene {s["status"]}">
  <div class="thumb">{img}</div>
  <div class="body">
    <div class="meta"><span class="tc">{s["t0"]:04.1f}–{s["t1"]:04.1f}s</span><span class="pill {s["status"]}">{lab[s["status"]]}</span></div>
    <p class="line">{html.escape(s["line"])}</p>
    <p class="look">{html.escape(s["look"])}</p>
  </div>
</li>''')
if st.get("preview"):
    player=f'<video id="player" controls playsinline preload="metadata" src="{st["preview"]}?v={ver}"></video>'
else:
    player='<div class="empty"><p>প্রথম রেন্ডার তৈরি হচ্ছে</p><span>সিন রেন্ডার হলেই ভিডিও এখানে চলে আসবে।</span></div>'
logs="".join(f"<li>{html.escape(x)}</li>" for x in st["log"])
page=f'''<title>Aminur Reel Edit</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600&family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
/* layout: editing-bay monitor on the left (sticky on wide screens), cut list on the right; one column on phones */
:root {{
  --bg:#eef4fb; --panel:#ffffff; --ink:#0d1b2a; --mute:#5b6b7e; --line:#d5e0ec;
  --accent:#0a84d6; --glow:#19c2f5; --ok:#12805a; --okbg:#dff5ea; --run:#a35a00; --runbg:#ffecc7; --idlebg:#e6edf5;
  --display:"Space Grotesk","Hind Siliguri",system-ui,sans-serif;
  --text:"Hind Siliguri","Inter",system-ui,sans-serif;
  --mono:"JetBrains Mono",ui-monospace,Menlo,monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg:#050b14; --panel:#0c1622; --ink:#e8f1fa; --mute:#8a9bb0; --line:#1b2a3c;
  --accent:#4db5ff; --glow:#19c2f5; --ok:#5fe0ae; --okbg:#0f3a2b; --run:#ffc36b; --runbg:#3d2a08; --idlebg:#152232; color-scheme:dark }} }}
:root[data-theme="dark"] {{
  --bg:#050b14; --panel:#0c1622; --ink:#e8f1fa; --mute:#8a9bb0; --line:#1b2a3c;
  --accent:#4db5ff; --glow:#19c2f5; --ok:#5fe0ae; --okbg:#0f3a2b; --run:#ffc36b; --runbg:#3d2a08; --idlebg:#152232; color-scheme:dark }}
body {{ background:var(--bg); color:var(--ink); font-family:var(--text); font-size:16px; line-height:1.5;
  padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)); padding-block:24px 48px; }}
.wrap {{ max-width:1040px; margin:0 auto; display:grid; gap:24px; }}
header {{ display:grid; gap:10px; }}
h1 {{ font-family:var(--display); font-size:clamp(26px,5vw,38px); line-height:1.1; margin:0; letter-spacing:-0.02em; text-wrap:balance; }}
.sub {{ color:var(--mute); margin:0; }}
.bar {{ height:8px; background:var(--idlebg); border-radius:99px; overflow:hidden; }}
.bar i {{ display:block; height:100%; width:{100*done/n:.0f}%; background:linear-gradient(90deg,var(--accent),var(--glow)); border-radius:99px; }}
.count {{ font-family:var(--mono); font-size:13px; color:var(--mute); display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; }}
.cols {{ display:grid; gap:24px; grid-template-columns:minmax(0,340px) minmax(0,1fr); align-items:start; }}
.monitor {{ position:sticky; top:calc(env(safe-area-inset-top, 0px) + 16px); display:grid; gap:12px; }}
.screen {{ background:#000; border-radius:18px; overflow:hidden; aspect-ratio:9/16; max-width:100%; border:1px solid var(--line); display:grid; }}
.screen video {{ width:100%; height:100%; object-fit:contain; background:#000; }}
.empty {{ place-self:center; text-align:center; padding:24px; color:#c9d8e8; }}
.empty p {{ margin:0 0 6px; font-weight:600; font-size:18px; color:#fff; }}
.empty span {{ font-size:14px; }}
.stage {{ font-size:14px; color:var(--mute); margin:0; }}
.stage b {{ color:var(--ink); font-weight:600; }}
h2 {{ font-family:var(--display); font-size:15px; text-transform:uppercase; letter-spacing:.08em; color:var(--mute); margin:0 0 12px; font-weight:500; }}
ul {{ list-style:none; margin:0; padding:0; }}
.scenes {{ display:grid; gap:10px; }}
.scene {{ display:grid; grid-template-columns:54px minmax(0,1fr); gap:14px; padding:12px; background:var(--panel); border:1px solid var(--line); border-radius:14px; }}
.scene.doing {{ border-color:var(--accent); }}
.thumb img, .ph {{ width:54px; aspect-ratio:9/16; border-radius:8px; object-fit:cover; display:block; background:var(--idlebg); }}
.body {{ min-width:0; display:grid; gap:4px; align-content:start; }}
.meta {{ display:flex; gap:10px; align-items:center; justify-content:space-between; }}
.tc {{ font-family:var(--mono); font-size:12px; color:var(--mute); font-variant-numeric:tabular-nums; }}
.pill {{ font-size:12px; font-weight:600; padding:2px 10px; border-radius:99px; background:var(--idlebg); color:var(--mute); }}
.pill.done {{ background:var(--okbg); color:var(--ok); }}
.pill.doing {{ background:var(--runbg); color:var(--run); }}
.line {{ margin:0; font-family:"Inter",var(--text); font-size:15px; font-weight:500; }}
.look {{ margin:0; font-size:14px; color:var(--mute); }}
.log {{ display:grid; gap:6px; font-size:14px; color:var(--mute); }}
.log li::before {{ content:"›"; color:var(--accent); margin-right:8px; }}
@media (max-width:760px) {{ .cols {{ grid-template-columns:minmax(0,1fr); }} .monitor {{ position:static; }} .screen {{ max-width:300px; margin:0 auto; width:100%; }} }}
</style>
<div class="wrap">
  <header>
    <h1>Aminur Reel Edit</h1>
    <p class="sub">এডিট যত এগোবে, এই পেজ নিজে থেকে আপডেট হবে।</p>
    <div class="bar" role="progressbar" aria-valuemin="0" aria-valuemax="{n}" aria-valuenow="{done}"><i></i></div>
    <div class="count"><span>{bn(done)} / {bn(n)} সিন তৈরি</span><span>মোট ৩৪.৩ সেকেন্ড · 1080×1920 · 30fps</span></div>
  </header>
  <div class="cols">
    <section class="monitor" aria-label="সর্বশেষ রেন্ডার">
      <div class="screen">{player}</div>
      <p class="stage">এখন চলছে: <b>{html.escape(st["stage"])}</b></p>
    </section>
    <div style="display:grid;gap:28px;min-width:0">
      <section><h2>কাট লিস্ট</h2><ul class="scenes">{"".join(rows)}</ul></section>
      <section><h2>যা হয়েছে</h2><ul class="log">{logs}</ul></section>
    </div>
  </div>
</div>
'''
open(D+"/aminur-reel-edit.html","w").write(page)
print("ok",len(page))
