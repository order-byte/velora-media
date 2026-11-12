# Aminur Rex SFX Pack — landing page

A fast, static landing page for selling the Aminur Rex sound-effects pack to video editors.
Apple-style UI in the Files-app sky blue, with light and dark mode.

No framework and no build step. It is plain HTML, CSS and JS, so it runs on any static host.

## What's on the page

- **Hero**: headline, launch price (₹199 → **₹99**), Buy button, and an editor-timeline mock with a **Play the edit** demo.
- **Sound previews**: tap-to-play cards with real waveforms.
- **Features** (bento grid), **How it works** (3 steps), **Pricing** card, **FAQ** and a final call to action.
- **Currency**: visitors in India see **₹ INR**. Everyone else sees **$ USD**, converted at the live exchange rate.
  An iOS-style switch lets anyone change currency, and the choice is remembered.
- **Mobile**: a sticky bottom **Buy** bar, plus a bottom-sheet checkout summary.

## Editing — `assets/js/config.js`

Almost everything you'll want to change is in this one file:

| Setting | What it does |
| --- | --- |
| `price.inr` / `price.inrOriginal` | Sale price and the struck-through price, in rupees. |
| `fixedUSD` | `null` converts INR → USD at the live rate. Set `{ price: 2.99, original: 5.99 }` to use your own dollar prices. |
| `checkoutUrl.INR` / `checkoutUrl.USD` | Payment links (Razorpay, Cashfree, Instamojo, Gumroad, Lemon Squeezy…). While both are empty, **Buy** opens a "checkout opening soon" sheet. |
| `contact` | Optional email / WhatsApp / Instagram links for the footer and checkout sheet. |
| `previews` | The sound cards. Set `src` to a real preview file, e.g. `assets/audio/whoosh.mp3`. |

Text such as headlines, features, FAQ and license wording is in `index.html`.

### Adding real sound previews

1. Put short preview files (mp3/m4a/wav) in `assets/audio/`.
2. Set each preview's `src` in `config.js`.

Until a preview has a `src`, the page plays a demo sound generated in the browser and shows a small
"Demo previews" note. That note disappears once every preview has a real file.

### Editor logos ("works with" strip)

The logos are files in `assets/logos/`. To change one, replace its file with a square image (SVG or PNG, at least 128 px)
and keep the name, or add a new `<li class="logo-chip">` in `index.html`. The two rows loop automatically.

Each logo gets a glossy finish and an occasional moving glint automatically, shaped to the logo itself.

Sources: Premiere Pro from Wikimedia Commons and After Effects from the Iconify "logos" set; Final Cut Pro,
DaVinci Resolve, CapCut, Alight Motion and Filmora are cut-outs of icon images supplied by the site owner.
All logos are trademarks of their owners and are shown only to say which apps the pack works with.

### Before launch, double-check

These are written as sensible defaults. Change them if they don't match your actual terms:

- "Royalty-free" / client-use license wording (features, pricing list, FAQ)
- "Free future updates"
- "Instant download link" (depends on your payment provider)
- If you charge a fixed dollar amount at checkout, set `fixedUSD` so the page shows the same price.

## Run locally

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000.

## Deploy

Upload the folder to any static host: GitHub Pages (Settings → Pages → deploy from branch), Netlify, Vercel or Cloudflare Pages.

## Files

```
index.html             Page markup and copy
assets/css/styles.css  Design system and layout
assets/js/config.js    Prices, checkout links, previews
assets/js/main.js      Currency, audio previews, buy flow, animations
assets/logos/          Editor app logos for the "works with" strip
assets/favicon.svg     App icon
```
