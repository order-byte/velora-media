# Aminur (@aminur_rex): Fiverr gig kit

Motionpeak-এর SaaS explainer gig দেখে বানানো। সব ভিডিও, ইমেজ আর লেখা Aminur-এর আসল client প্রজেক্ট থেকে।

## কী কী আছে

| ফাইল | কী |
|---|---|
| `media/aminur-showreel-gig-video.mp4` | Gig ভিডিও: ৫৩.৫ সেকেন্ড, 1920×1080, 30 fps, ৩৮ MB, মিউজিক Rising Forest। Fiverr limit: ৭৫ সেকেন্ড, ৫০ MB |
| `media/gig-image-1-thumbnail.jpg` | Image 1: thumbnail (search-এ এটাই দেখা যায়) |
| `media/gig-image-2-recent-work.jpg` | Image 2: recent client work |
| `media/gig-image-3-how-we-work.jpg` | Image 3: no middlemen + ৪ ধাপের প্রসেস |
| `gig-copy.md` | Title, প্যাকেজ, description, FAQ, requirements, tags: সব লেখা |
| `claude-chrome-prompt.md` | Claude in Chrome-এ paste করার prompt |
| `build/` | Reel, মিউজিক আর ইমেজ বানানোর স্ক্রিপ্ট (পরে বদলাতে চাইলে) |

## ধাপগুলো

1. কম্পিউটারের **Downloads** ফোল্ডারে একটা নতুন ফোল্ডার বানাও, নাম দাও **`Aminur-Fiverr-Gig`**।
2. `media/` ফোল্ডারের ৪টা ফাইল ওই ফোল্ডারে রাখো:
   - `aminur-showreel-gig-video.mp4`
   - `gig-image-1-thumbnail.jpg`
   - `gig-image-2-recent-work.jpg`
   - `gig-image-3-how-we-work.jpg`
3. Chrome-এ Fiverr খোলো, **aminur_rex** দিয়ে লগইন করা থাকতে হবে।
4. Claude extension খোলো, `claude-chrome-prompt.md`-এর বক্সের ভিতরের পুরো লেখা copy করে paste করো।
5. Claude নিজে Overview, Pricing, Description, FAQ, Requirements সব ভরবে। Gallery-তে এসে নিজে ফাইল বেছে নিতে না পারলে তোমাকে বলবে, তখন ওই ৪টা ফাইল drag করে দিও, তারপর "done" লিখো।
6. শেষে Claude একটা summary দেখাবে, Publish করবে না। সব ঠিক থাকলে লিখো **"publish"**।

## Sound আর মিউজিক

- **মিউজিক:** "Rising Forest" by Diego Nava (Mixkit, House, 124 BPM)। Mixkit Stock Music Free License: online ads, social video, website-এ commercial ব্যবহার চলবে, credit লাগবে না। বিস্তারিত `MUSIC-LICENSE.md`-এ।
- ট্র্যাকটা rubberband দিয়ে 128.6 BPM-এ আনা হয়েছে (+3.7%, pitch একই), তারপর bar ধরে কাটা: intro → drop → breakdown → drop → শেষ hit। প্রতিটা kick ভিডিওর কাটের ±৮ ms-এর মধ্যে পড়ে।
- আরও ২টা অপশন তৈরি আছে: "Techno Fest Vibes" (Alejandro Magaña) আর "Cat Walk" (Arulo)। বদলাতে চাইলে বলো, শুধু অডিও বদলাতে হবে।
- **Sound effects:** v1 (Commas Affiliate Center) থেকে আসল whoosh, impact, riser, pop, click কেটে নেওয়া, মিউজিকের ২-৪ dB উপরে।
- Loudness: −14 LUFS, peak −1.6 dB।

## Publish করার আগে দেখে নাও

- **Voice over, 9:16 ভার্সন, subtitles:** প্যাকেজ আর FAQ-তে এগুলোর কথা আছে। তোমার টিম এগুলো দিতে না পারলে বাদ দাও।
- **"Over 2,000 videos delivered"** তোমার প্রোফাইল থেকে নেওয়া। সত্যি হলেই রাখো।
- **CSGOGem** (case battle / skin gambling) ভিডিও আর ইমেজ থেকে ইচ্ছা করে বাদ। Fiverr gambling-এর gig আটকাতে বা flag করতে পারে।
- **Noor Motion**-এর নাম reel আর Image 2-তে client হিসেবে আছে। এটা অন্য স্টুডিও হলে বলো, বাদ দিয়ে দেব।
- দাম: $150 / $290 / $490 (reference-এর চেয়ে ~৩০% কম)। ৫-১০টা ভালো review-এর পর বাড়িয়ে দিও।
