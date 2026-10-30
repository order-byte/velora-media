"""Hindi voiceover with Veena (maya-research/Veena, Apache-2.0) on CPU.
Usage: python veena_tts.py <speaker> <out_dir> [line_index ...]"""
import glob, json, os, subprocess, sys, time
import numpy as np
import soundfile as sf
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from snac import SNAC

HF = "/tmp/claude-0/-home-user-velora-media/66ff1a82-31ea-5c05-a6ba-b6463a076dc9/scratchpad/hf"
LIVE = "/tmp/claude-0/-home-user-velora-media/66ff1a82-31ea-5c05-a6ba-b6463a076dc9/scratchpad/live/live.py"
LINES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lines.json")))

SOS, EOS, SOH, EOH, SOA, EOA, BASE = 128257, 128258, 128259, 128260, 128261, 128262, 128266


def live(stage, detail, progress=-1.0):
    subprocess.run([sys.executable, LIVE, "status", stage, detail, str(progress)], check=False)


def decode(tokens, snac):
    tokens = tokens[: len(tokens) // 7 * 7]
    lv = [[], [], []]
    off = [BASE + i * 4096 for i in range(7)]
    for i in range(0, len(tokens), 7):
        lv[0].append(tokens[i] - off[0])
        lv[1] += [tokens[i + 1] - off[1], tokens[i + 4] - off[4]]
        lv[2] += [tokens[i + 2] - off[2], tokens[i + 3] - off[3], tokens[i + 5] - off[5], tokens[i + 6] - off[6]]
    codes = [torch.tensor(l, dtype=torch.int32).unsqueeze(0) for l in lv]
    with torch.no_grad():
        return snac.decode(codes).squeeze().clamp(-1, 1).numpy()


def main():
    speaker, out = sys.argv[1], sys.argv[2]
    which = [int(x) for x in sys.argv[3:]] or list(range(len(LINES)))
    os.makedirs(out, exist_ok=True)
    torch.set_num_threads(4)
    path = glob.glob(f"{HF}/models--maya-research--Veena/snapshots/*")[0]
    snac_path = glob.glob(f"{HF}/models--hubertsiuzdak--snac_24khz/snapshots/*")[0]
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(path)
    model = AutoModelForCausalLM.from_pretrained(path, torch_dtype=torch.bfloat16).eval()
    snac = SNAC.from_pretrained(snac_path).eval()
    print(f"loaded in {time.time() - t0:.0f}s", flush=True)
    for n, i in enumerate(which):
        text = LINES[i]
        live("Voiceover: Veena (free Hindi AI voice)", f"Line {i + 1} of {len(LINES)}: {text}", n / len(which))
        ids = tok.encode(f"<spk_{speaker}> {text}", add_special_tokens=False)
        inp = torch.tensor([[SOH, *ids, EOH, SOA, SOS]])
        max_new = min(int(len(text) * 1.3) * 7 + 21, 700)
        t1 = time.time()
        torch.manual_seed(1234 + i)
        with torch.no_grad():
            gen = model.generate(inp, max_new_tokens=max_new, do_sample=True, temperature=0.4, top_p=0.9,
                                 repetition_penalty=1.05, pad_token_id=tok.pad_token_id, eos_token_id=[EOS, EOA])
        new = gen[0][inp.shape[1]:].tolist()
        codes = [t for t in new if BASE <= t < BASE + 7 * 4096]
        audio = decode(codes, snac)
        sf.write(os.path.join(out, f"line_{i:02d}.wav"), audio, 24000)
        print(f"line {i}: {len(new)} tokens in {time.time() - t1:.0f}s -> {len(audio) / 24000:.1f}s audio, "
              f"ended={'yes' if (EOS in new or EOA in new) else 'NO (hit max)'}", flush=True)
    live("Voiceover done", f"{len(which)} lines generated with Veena", 1.0)


if __name__ == "__main__":
    main()
