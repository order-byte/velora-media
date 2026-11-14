# Aminur Rex SFX Pack — Promo voiceover script

The voiceover follows the reference video beat for beat, so every line has the same time slot as the reference.

## ElevenLabs settings

- **Voice:** Emma - Youthful, Upbeat Commercial (voice ID `nyfVCF0XNA1BwwJ7FiP2`)
  - Backup voice: Kristen - Natural Upbeat Conversational Ad (`dfeOmy6Uay63tNhyO99j`)
- **Model:** Eleven Multilingual v2
- **Stability:** 40% · **Similarity:** 75% · **Style:** 25% · **Speed:** 1.05
- **Output:** MP3 44.1 kHz 192 kbps, or WAV

## Paste this into ElevenLabs (one generation, the whole script)

```
Want your edits to hit harder?
Say hello to Aminur Rex.
The best S.F.X. pack for editors.
Explore our massive sound library, and pick your favorite sound from a huge selection of whooshes, impacts, risers, glitches...
punchy sounds that hit just right, with crisp UI sounds as well.
Drag. Drop. Done.
You can't say Aminur Rex... without saying F.X.!
```

If "Aminur" comes out wrong, write it as `Ah-mee-noor Rex`.

## Timing (each line is placed in its slot automatically)

| # | Slot (sec) | Line | On screen |
|---|---|---|---|
| 1 | 0.0 – 1.7 | Want your edits to hit harder? | Kinetic words on black |
| 2 | 1.7 – 3.6 | Say hello to Aminur Rex. | Emoji, "Say hello to...", logo reveal |
| 3 | 3.6 – 5.9 | The best S.F.X. pack for editors. | Vinyl + CD, search bar typing |
| 4 | 5.9 – 12.7 | Explore our massive sound library, and pick your favorite sound from a huge selection of whooshes, impacts, risers, glitches... | Store page, then the 15-folder grid and cursor click |
| 5 | 12.8 – 14.4 | punchy sounds that hit just right, | "Punchy sounds that hit just right." |
| 6 | 14.4 – 16.3 | with crisp UI sounds as well. | Phone list of sounds |
| 7 | 16.3 – 17.5 | Drag. Drop. Done. | "Drag. Drop. Done." |
| 8 | 17.6 – 20.3 | You can't say Aminur Rex... without saying F.X.! | "You can't say [logo] without saying..." |
| — | 19.9 – 22.0 | (no voice) | End card: logo + @aminurrex |

## Audio layers

- **Sound effects:** taken from the reference video (`audio/sfx_track.wav`), separated from its voice and music, and timed to the same frames.
- **Music:** not included; it will be added later.
- **Voice:** your ElevenLabs file. `fit_vo.py` cuts it into the 8 lines and places each line in its slot.
