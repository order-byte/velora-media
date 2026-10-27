# Edit Brief: Transitions + After Effects / Premiere Pro Scene for My Reel

Hi Claude! I need help finishing a short vertical video (Instagram Reel). Please talk to me in Bengali (বাংলা).

## Background
I'm a freelance video editor. This reel shows how I made ₹21,000 from one 60-second video for a US company, **Offline IQ** (offlineiq.ai). Offline IQ makes private AI that runs inside a company's own office, with no internet. The reel is vertical (1080×1920) and under 60 seconds.

## I've already done the editing
All the cutting is done. The order, timing, voiceover, captions and music are final. The problem is that the cuts between scenes look rough and not professional.

## Your job: only these 2 things

### 1. Add transitions
- Add clean, professional transitions at the cuts so the reel flows smoothly.
- **Copy the transition style of the reference video** I'm attaching. If you can't play video directly, extract frames (for example with ffmpeg, one frame every 0.2 sec around each cut) and study those.
- Keep transitions fast so the reel doesn't slow down.
- Add a transition sound (like a light whoosh) only if the reference uses one, and keep it below my voice.
- **Change nothing else.** No re-cutting, no timing changes. Keep my voiceover, captions and music exactly as they are, and keep the same total length.

### 2. Create the After Effects + Premiere Pro scene
At one point in the reel I say: *"Then the real work. After Effects mein animations, Premiere Pro mein final edit — cuts, music, sound design."* While I say this, the screen should show me working in After Effects and then Premiere Pro. **I don't have screen recordings from that project, so please create this footage:**

1. **Research first.** Go to offlineiq.ai (home, Fort Knox and How It Works pages) so the project looks real. Note:
   - their headline: "Your AI. Inside your walls. Nothing leaves."
   - their product name: Fort Knox
   - their colours: orange #C77255, light background #ECF2EB, dark text #2F312F
2. **After Effects part** (first half):
   - Recreate the After Effects interface: dark theme, project panel, composition viewer, and a timeline with layers and keyframes.
   - Play **my real Offline IQ video** (`offlineiq_final_video`) inside the composition viewer at **2× speed**, with the playhead moving along the timeline.
   - Give the layers and comps realistic names based on your research, e.g. `Hero_Headline`, `FortKnox_Box`, `Nothing_Leaves_Text`, `Data_Lines`, `End_CTA`.
3. **Premiere Pro part** (second half):
   - Recreate the Premiere Pro interface: program monitor, plus a timeline with video and audio tracks and waveforms.
   - Play the same video in the program monitor at **2× speed**, with the playhead moving.
   - End with the export progress bar hitting 100%.
4. **Vertical and readable.** It must fit 1080×1920 and be readable on a phone. Zoom into the viewer and timeline rather than showing the whole tiny interface, or start wide and slowly push in.
5. **Exact length.** Match the exact length of that voiceover line in my cut. Switch from After Effects to Premiere Pro right when I say "Premiere Pro".
6. **Place it** in my cut at that spot, replacing whatever is there now.

## Files I'm attaching
| File | What it is |
|------|-----------|
| `my_edit` | My finished cut, with everything done except the transitions and the AE/Premiere scene |
| `offlineiq_final_video` | The real video I made for Offline IQ, to show inside the AE and Premiere interfaces |
| `reference_video` | Style reference for the transitions |

## Script (for context only; the timing in my cut is final)
1. **Hook:** "Ek 60-second video se ₹21,000 kamaye — ek din mein. Here's the process."
2. "It started with a message from a US company — Offline IQ."
3. **Meeting:** "First, a meeting. Client ne poora project samjhaya — product kya hai, video mein kya chahiye."
4. **WhatsApp:** "After the meeting, unhone saari details WhatsApp pe bhej di."
5. **Website:** "Then I studied their website — private AI, jo bina internet ke company ke andar chalta hai."
6. **Deal:** "Deal final hui — ₹20,000. And before starting, ₹10,000 advance aa gaya."
7. **AE + Premiere (the scene you create):** "Then the real work. After Effects mein animations, Premiere Pro mein final edit — cuts, music, sound design."
8. **Delivery:** "Video deliver kiya. Client ne ek small change maanga — maine fix karke wapas bhej diya."
9. **Payment:** "Then the final payment — ₹11,000. Baaki ₹10,000 tha, but client ne ₹1,000 extra diya. Total: ₹21,000."
10. **CTA:** "Ye client mujhe mila kaise? Comment 'CLIENT' — next video mein bataunga."

## Rules
- The final video must stay under 60 seconds and the same length as my cut.
- Don't change my cuts, voiceover, captions, music or the amounts shown.
- If you notice private info that isn't blurred (client names or faces, phone numbers, emails, transaction IDs), tell me. Don't change it yourself.

## What I want back
1. **First:** a short note on the transition style you'll copy from the reference, plus any questions.
2. **Then:** the final MP4 (1080×1920, 30 fps, H.264, same length as my cut). Also send the AE/Premiere scene as a separate clip.
3. **If you can't render video:** give me
   - a transition list: at each cut, the timestamp, which transition and how long it lasts
   - step-by-step instructions to build the AE/Premiere scene myself
