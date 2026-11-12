# Aminur Rex SFX Pack — landing page

A fast, static store page for the Aminur Rex sound-effects pack, built for video editors.
Apple-style UI in the Files-app sky blue, with light and dark mode.

**Live:** https://order-byte.github.io/velora-media/

There is no framework and no build step. The site is plain HTML, CSS and JS, served by GitHub Pages from `main`.

## What's on the page

- **Hero**: headline, launch price (₹199 → **₹99**) and Buy button.
- **Demo edit**: an editor timeline. **Play the edit** plays UI-style sounds that are generated in the browser for this page.
- **Works with**: real editor app logos in two slowly scrolling rows.
- **What's inside**: the pack's 14 category folders in a Files-style window, plus the key numbers.
- **Features**, **How it works**, and a **Pricing** card with trust points: secure checkout, payment options, instant delivery.
- **FAQ** and a final call to action.
- **Currency**: visitors in India see **₹ INR**. Everyone else sees an approximate **$ USD** price, and can switch.
- **Mobile**: a sticky Buy bar at the bottom.

## Payments and delivery

- Every **Buy** button opens the SuperProfile product page: https://superprofile.bio/vp/aminur-rex-sfx-pack
- SuperProfile takes payment by UPI, cards or netbanking. Buyers abroad pay in their own currency.
- After payment, SuperProfile delivers the pack and emails the download link. The pack's link is never in this site's code.
- `download.html` is a thank-you page that explains where buyers find their link.

## Editing — `assets/js/config.js`

| Setting | What it does |
| --- | --- |
| `price.inr` / `price.inrOriginal` | Sale price and the struck-through price, in rupees. |
| `fixedUSD` | `null` converts INR → USD at the live rate. Set `{ price: 2.99, original: 5.99 }` to use your own dollar prices. |
| `checkoutUrl.INR` / `checkoutUrl.USD` | Payment links. With only `INR` set, everyone uses that link. If both are empty, **Buy** opens a "checkout opening soon" sheet. |
| `delivery.method` | `"platform"` (live): the payment platform delivers the pack. `"link"`: a button to `delivery.fullPackUrl`, which is publicly visible. `"zip"`: ZIPs built by `tools/build_pack.py`. |
| `testMode` | `true` adds a "Test purchase" button to the checkout sheet. Keep `false` on the live site. |
| `contact` | Optional email / WhatsApp / Instagram links for the footer and help text. |

All page text (headlines, features, FAQ, license wording) is in `index.html`.

### Editor logos

The logos are files in `assets/logos/`. To change one, replace its file with a square image (SVG or PNG, at least 128 px)
and keep the same name. Each logo gets a glossy finish and an occasional glint automatically.

Sources: Premiere Pro from Wikimedia Commons and After Effects from the Iconify "logos" set. Final Cut Pro,
DaVinci Resolve, CapCut, Alight Motion and Filmora are cut-outs of icon images supplied by the site owner.
All logos are trademarks of their owners and are shown only to say which apps the pack works with.

## Updating the live site

Changes merged into `main` go live on GitHub Pages within a minute or two.

## Run locally

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000.

## Files

```
index.html             Store page markup and copy
download.html          Thank-you page after payment
assets/css/styles.css  Design system and layout
assets/js/config.js    Prices, checkout link, delivery settings
assets/js/main.js      Currency, demo edit audio, buy flow, animations
assets/js/download.js  Thank-you page behaviour
assets/logos/          Editor app logos
assets/favicon.svg     App icon
tools/build_pack.py    Optional: builds ZIPs + manifest from pack/ (for delivery.method "zip")
.nojekyll              Tells GitHub Pages to serve files as they are
```
