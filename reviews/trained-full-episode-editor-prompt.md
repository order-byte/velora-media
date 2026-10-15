# Fix list for "TrAIned_Full_Episode_1080p.mp4" (v1, 13:31.76, 1080p25)

You edited this episode. Below is a frame- and waveform-checked list of problems in your v1 render. Fix every item in "MUST FIX", then apply "SHOULD FIX". Do not change anything that is not listed.

## Rules

- All timecodes are **v1 timecodes** (the file you rendered, total length 13:31.76). Every cut shifts later times. Work from the **end of the video backwards**, or locate each item by its words, not just by time.
- Every audio cut gets a 10–20 ms crossfade. No hard cuts, no dropouts, no clicks.
- After each cut, check that the video still matches the voice (lip sync) and that no single "flash" frame of another shot is left behind.
- Keep the output format: 1920x1080, 25 fps, AAC 48 kHz stereo, integrated loudness about −14 LUFS, true peak ≤ −1 dBTP. These are already correct; don't change them.
- When you're done, return a change log: each item number, what you did, and the new timecode.

---

## MUST FIX

### A. A speech clip was pasted under the chapter and callout cards (main audio bug)

One short clip of the presenter saying **"And if you're wa—"** (≈1.3 s) was placed as the "transition sound" under every chapter card and red callout card. Most of the time it plays twice in a row ("and if you're what… and if you're what…"). The waveform is identical every time (correlation 0.99–1.00), so it is a copy, not real narration.

Delete the clip at each spot below. If a card needs a sound, use a short, soft whoosh or riser SFX, peaking at least 8–10 dB below the voice. Never use speech.

| # | v1 time | Card on screen | What should remain |
|---|---|---|---|
| A1 | 0:47.8 – 0:49.3 | red card "Which one is LYING?" | "…So which one is lying? **Give me two minutes** and you'll see exactly what each one is measuring." |
| A2 | 1:18.7 – 1:21.5 | chapter 01 "The two reports" | "…and this is TrAIned. **The happy number** comes from…" |
| A3 | 2:52.3 – 2:55.3 | chapter 02 "Who was fixing it?" | "…exposed everything else. **To find out who was fixing it**, come with me…" |
| A4 | 5:01.3 – 5:04.5 | chapter 03 "The blue screen" | "…became a real problem. **That blue screen is Turbo C++**…" |
| A5 | 5:48.0 – 5:51.0 | chapter 04 "The exam" | "…the numbers in a minute. **But the bigger problem**, ladies and gentlemen, isn't the software…" |
| A6 | 7:23.6 – 7:26.9 | chapter 05 "The machine" | "…how rarely students actually use it. **University syllabus isn't like an iPhone app**…" |
| A7 | 9:35.8 – 9:37.6 | red card "What's left for the engineer?" | "…what's left for the engineer to be good at? **Hold that thought.** The answer isn't prompting." |
| A8 | 10:38.1 – 10:40.6 | chapter 06 "What should you do?" | "…the student only gets one degree. **So what should a student actually do?**" |
| A9 | 13:27.8 – 13:31.8 | end card "TrAIned" | Replace with a music sting or end music and fade out. Right now the audio stops abruptly mid-loop. |

**Do not touch 0:54.5 – 0:57.8** ("And if you're watching this from outside India, stay with me."). This is the one place where the presenter really says the line.

### B. Retakes, false starts and stutters you left in

| # | v1 time | Now sounds like | Fix |
|---|---|---|---|
| B1 | 2:07.5 – 2:08.6 | "no job offer, **no internship,** no internship offer either" | Cut the first "no internship," |
| B2 | 2:37.5 – 2:38.6 | "never noticed **because somebody** because somebody was quietly fixing it" | Cut the first "because somebody" |
| B3 | 5:22.2 – 5:24.1 | "**To run it today, you didn't—** To run it today, you need an emulator" | Cut the false start. Keep the second take. |
| B4 | 7:31.9 – 7:32.7 | "push an update overnight. **Syllabus—** A syllabus has to pass through layers" | Cut the stray "Syllabus" |
| B5 | 7:38.7 – 7:39.7 | "each one exists for a reason. **And stuff—** At the top sits AICTE" | Cut "and stuff" |
| B6 | 7:48.3 – 7:50.3 | "a template **that universities asked—** that universities are asked to adopt" | Cut the first attempt |
| B7 | 8:37.2 – 8:38.0 | "the same morning, **in colleges,** in colleges whose labs range…" | Cut the first "in colleges" |
| B8 | 7:58.6 – 7:59.8 | "don't write their own syllabus. *(mumble/gap)* …writes it and sets the exams" | The sentence has lost its subject (e.g. "The university they're affiliated to writes it"). Restore the full line from the raw take. If no clean take exists, cut the mumble and put on-screen text "→ The affiliating university writes it". |
| B9 | 11:02.4 – 11:02.7 | "hard to spot. **Or… or** crawls once the data gets big" | Check this one. If "or" is doubled, cut the first one. |

### C. Damaged words, hard cuts and a factual error

| # | v1 time | Problem | Fix |
|---|---|---|---|
| C1 | 5:18.0 – 5:19.4 | The year should be "nineteen ninety-**one**", but the "-one" is cut off, so it sounds like "1990". There is a hard splice with a 60 ms dropout at 5:19.28. | Restore the full word "1991" from the raw take and crossfade. If that's not possible, at least remove the dropout and show "1991" on screen. |
| C2 | 8:30.5 | Hard cut with a 70 ms dropout between "It's arithmetic." and "The paper exams…" | 10–20 ms crossfade plus room tone |
| C3 | 10:28.3 – 10:28.6 | The VO says "ChatGPT only arrived at the end of **2020**". That's wrong: ChatGPT launched in Nov 2022, and your own on-screen text says "end of 2022". | Best: use a correct take from the raw footage. If none exists, cut the clause "ChatGPT only arrived at the end of 2020" and keep the on-screen "ChatGPT arrived end of 2022". |

### D. Visual errors

| # | v1 time | Problem | Fix |
|---|---|---|---|
| D1 | 4:33.6 – 4:48.8 | **Graphics are in the wrong order.** The Infosys chart (50,000+ → under 12,000, −76%) plays at 4:33.6–4:40.4, while the VO is talking about the whole IT sector ("60–70k freshers, lowest in 20 years", 4:33.0–4:40.6). Then the text "60–70k freshers. Lowest in 20 years." shows at 4:40.8–4:48.8, while the VO is already saying "Infosys alone went from 50,000 to under 12,000" (4:41.0–4:45.9). | Swap them: the "60–70k / lowest in 20 years" visual goes with the IT-sector line, and the Infosys bar chart goes with the "Infosys alone…" line. |
| D2 | 5:04.4 – 5:04.9 | **Flash frame.** The presenter shot pops up for about half a second between the chapter card "03 The blue screen" and the Turbo C++ screen. | Remove it. Go straight from the card to the blue screen. |
| D3 | 0:46.9 – 0:49.6 | "Which one is lying?" appears twice in a row: first as kinetic text (0:46.9–0:47.9), then as the red sticky card (0:48.0–0:49.6). | Keep only one. Once A1 is fixed, the red card has no audio under it, so drop the red card. |
| D4 | 9:32.0 – 9:37.6 | Same problem: the text "AI writes the code. What's left?" is followed immediately by the red card "What's left for the engineer?" | Keep only one. |
| D5 | 10:38.5 – 10:43.3 | The chapter card "What should you do?" is followed immediately by the big caption "WHAT SHOULD YOU DO?" (10:41.7–10:43.3). | Remove the caption. |
| D6 | 13:25.6 – 13:27.7 | **Outtake footage is left in.** After "I'll see you there." the presenter scratches his head, waves, and leans in toward the camera to stop recording. | End the A-roll at about 13:25.6, right after "…see you there." |
| D7 | 13:27.8 – 13:28.1 | Black flash frame (0.32 s) before the logo | Remove it. Use a clean transition. |
| D8 | 13:28.1 – 13:31.8 | The end card lasts only 3.7 s, with nowhere to place YouTube end-screen elements. At 13:24.3 the presenter points to the upper right ("it's right there"), but nothing is there. | Make a 10–20 s end screen with a video placeholder where he points, plus a subscribe element. Use music under it and fade out. |

### E. Audio clean-up (whole video)

- E1. A constant low hum of about **55.7 Hz** runs through the whole video (≈ −49 dBFS, easiest to hear in pauses). Fix it with a high-pass filter at 70–80 Hz, or a narrow notch at 55.7 Hz. Don't thin out the voice.
- E2. In pauses the noise floor rises by about 3 dB (compressor pumping). Use a gentler compression release, or a light expander, so pauses stay steady.
- Already fine, keep as is: −14.0 LUFS integrated, −1.2 dBFS peak, no clipping, mono-compatible voice.

---

## SHOULD FIX (polish)

1. **Pacing.** The VO runs at about 170 words per minute and the longest pause is 0.8 s. Add 0.3–0.6 s of breathing room after the big reveals: after "the lowest in 20 years" (4:40.6), after the Aspiring Minds numbers (about 6:49), after "the student only gets one degree" (10:38). The chapter cards make good beats once the speech loop is replaced.
2. **Chapter cards.** Each one opens with a 0.4–0.6 s near-empty gradient frame (for example 1:19.2, 5:01.8, 10:38.6). Bring the title in sooner, or shorten the cards to about 1.5–2 s.
3. **Overlay clutter.** Two text overlays sometimes sit on screen at once, e.g. 2:32–2:35 ("Not a new gap" / "20 years" plus the bottom caption) and 8:54–8:58 ("A fairness machine" plus "THE SYSTEM ISN'T STUPID"). Show one at a time.
4. **Small source tags.** The lower-left tags (e.g. "India Skills Report 2025 · Wheebox" 1:22, "Unstop survey" 1:56, "Turbo C++ 3.0" 5:12, "Watch next" 13:24) use about 20 px text, which is too small on phones. Raise them to about 30–36 px.
5. The presenter says "Borland" quickly (around 5:07). Add "Borland" to the Turbo C++ caption so viewers catch the name.
6. **Music bed (optional).** There is no audible background music except a short swell at 13:26. A very low bed (about 25–30 dB under the voice, ducked under speech) would help the chapter transitions. Skip this if the dry sound is a deliberate choice.

## Deliverables

1. v2 render with the same specs.
2. A change log covering A1–A9, B1–B9, C1–C3, D1–D8, E1–E2 (and any SHOULD FIX items you applied), with the new timecodes.
3. If an item could not be fixed because there is no clean raw take (B8, C1, C3), say so explicitly and describe the workaround you used.
