"""Cut the showreel excerpts out of Aminur's project videos and bring them all to
crisp 1920x1080 @ 60fps.

  * 4K sources       -> lanczos downscale (already sharp)
  * 1080p30 sources  -> motion-interpolated to 60fps
  * 736x414 sources  -> Real-ESRGAN x4 upscale, then interpolated to 60fps

Outputs per clip:
  assets/work/hq/<id>.mp4            1080p60 master (CRF 12)
  assets/work/frames/<id>/NNNN.jpg   exact frames for the renderer
  assets/work/preview/<id>.mp4       light 960x540 copy for the live preview
and assets/work/clips.js describing them.

usage: python3 tools/prepare_work.py [--only id,id] [--esrgan-weights path]
"""
import json, os, subprocess, sys, shutil, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, 'assets/work/raw')
OUT = os.path.join(ROOT, 'assets/work')
TMP = os.environ.get('PREP_TMP', os.path.join(ROOT, 'out/prep_tmp'))

# id: (source, start, duration, kind, label)
CLIPS = {
    'csgo_pick':     ('csgogem.mp4',      5.4, 3.0, '4k',  'CSGOGem · Launch promo'),
    'csgo_mines':    ('csgogem.mp4',     15.6, 3.0, '4k',  'CSGOGem · Mines'),
    'csgo_deposit':  ('csgogem.mp4',     27.2, 3.0, '4k',  'CSGOGem · Payments'),
    'nano_orbit':    ('nanosyllabus.mp4', 0.8, 1.8, '4k',  'NanoSyllabus · EdTech promo'),
    'nano_science':  ('nanosyllabus.mp4', 38.6, 3.0, '4k', 'NanoSyllabus · Concepts'),
    'nano_explore':  ('nanosyllabus.mp4', 45.0, 3.0, '4k', 'NanoSyllabus · Explore'),
    'fort_walls':    ('fortknox.mp4',     0.3, 3.0, 'hd30', 'OfflineIQ · Fort Knox'),
    'fort_apps':     ('fortknox.mp4',    63.5, 3.0, 'hd30', 'OfflineIQ · Workflows'),
    'quad_globe':    ('quadrant.mp4',     2.6, 3.0, 'hd30', 'Quadrant · IT Services'),
    'quad_insight':  ('quadrant.mp4',    26.0, 3.0, 'hd30', 'Quadrant · Data to insight'),
    'flowly_glass':  ('balcony_pin.mp4',  0.0, 2.4, 'low', 'Flowly · AI notes'),
    'flowly_phone':  ('balcony_pin.mp4',  4.0, 1.6, 'low', 'Flowly · App UI'),
    'flowly_grass':  ('balcony_pin.mp4',  6.0, 2.4, 'low', 'Flowly · Listening'),
    'agent_boost':   ('habit_pin.mp4',   14.2, 1.8, 'low', 'AI Agent · Boost'),
    'agent_glass':   ('habit_pin.mp4',   16.2, 1.8, 'low', 'AI Agent · Glass UI'),
}

MI = 'minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1'


def run(cmd):
    print('+', ' '.join(cmd[:6]), '...', flush=True)
    subprocess.run(cmd, check=True)


def master(cid, weights):
    src, start, dur, kind, _ = CLIPS[cid]
    hq = os.path.join(OUT, 'hq', f'{cid}.mp4')
    if os.path.exists(hq):
        return hq
    os.makedirs(os.path.dirname(hq), exist_ok=True)
    srcp = os.path.join(RAW, src)
    enc = ['-c:v', 'libx264', '-preset', 'slow', '-crf', '12', '-pix_fmt', 'yuv420p', '-an']
    if kind == '4k':
        vf = 'fps=60,scale=1920:1080:flags=lanczos+accurate_rnd+full_chroma_int'
        run(['ffmpeg', '-v', 'error', '-y', '-ss', str(start), '-t', str(dur), '-i', srcp, '-vf', vf, *enc, hq])
    elif kind == 'hd30':
        vf = f'{MI},unsharp=3:3:0.35'
        run(['ffmpeg', '-v', 'error', '-y', '-ss', str(start), '-t', str(dur), '-i', srcp, '-vf', vf, *enc, hq])
    else:  # low-res: ESRGAN at 30fps, then interpolate to 60
        d_in = os.path.join(TMP, cid, 'in'); d_up = os.path.join(TMP, cid, 'up')
        os.makedirs(d_in, exist_ok=True)
        if not glob.glob(os.path.join(d_in, '*.png')):
            run(['ffmpeg', '-v', 'error', '-y', '-ss', str(start), '-t', str(dur), '-i', srcp, '-vf', 'fps=30', os.path.join(d_in, '%04d.png')])
        run([sys.executable, '-I', os.path.join(HERE, 'esrgan.py'), weights, d_in, d_up, '1920', '1080'])
        run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(d_up, '%04d.png'), '-vf', MI, *enc, hq])
    return hq


def derive(cid):
    hq = os.path.join(OUT, 'hq', f'{cid}.mp4')
    fdir = os.path.join(OUT, 'frames', cid)
    if not glob.glob(os.path.join(fdir, '*.jpg')):
        os.makedirs(fdir, exist_ok=True)
        run(['ffmpeg', '-v', 'error', '-y', '-i', hq, '-q:v', '2', os.path.join(fdir, '%04d.jpg')])
    prev = os.path.join(OUT, 'preview', f'{cid}.mp4')
    if not os.path.exists(prev):
        os.makedirs(os.path.dirname(prev), exist_ok=True)
        run(['ffmpeg', '-v', 'error', '-y', '-i', hq, '-vf', 'scale=960:540', '-c:v', 'libx264', '-preset', 'slow', '-crf', '24',
             '-g', '15', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', prev])
    return len(glob.glob(os.path.join(fdir, '*.jpg')))


def main():
    args = sys.argv[1:]
    only = None
    weights = os.environ.get('ESRGAN_WEIGHTS', '')
    if '--only' in args:
        only = args[args.index('--only') + 1].split(',')
    if '--esrgan-weights' in args:
        weights = args[args.index('--esrgan-weights') + 1]
    ids = [c for c in CLIPS if not only or c in only]
    for cid in ids:
        master(cid, weights)
        derive(cid)
    # describe every clip that is ready
    meta = {}
    for cid, (_, _, _, kind, label) in CLIPS.items():
        fdir = os.path.join(OUT, 'frames', cid)
        n = len(glob.glob(os.path.join(fdir, '*.jpg')))
        if n:
            meta[cid] = {'frames': n, 'fps': 60, 'label': label}
    with open(os.path.join(OUT, 'clips.js'), 'w') as f:
        f.write('// written by tools/prepare_work.py\nwindow.CLIPS = ' + json.dumps(meta, indent=1) + ';\n')
    print('clips ready:', ', '.join(meta))


if __name__ == '__main__':
    main()
