/*
 * ─────────────────────────────────────────────────────────────
 *  Aminur Rex SFX Pack — store settings
 *  Edit this file to change prices, checkout links and previews.
 *  No build step: save the file and refresh the page.
 * ─────────────────────────────────────────────────────────────
 */
window.STORE_CONFIG = {
  brand: "Aminur Rex",
  productName: "Aminur Rex SFX Pack",

  /* Prices in Indian Rupees. `inrOriginal` is shown struck through. */
  price: {
    inr: 99,
    inrOriginal: 199,
  },

  /*
   * Buyers outside India see US dollars.
   *  - Leave `fixedUSD` as null to convert the INR price at the live exchange rate.
   *  - Or set your own dollar prices, e.g. { price: 2.99, original: 5.99 }.
   *    Do this if your USD checkout charges a fixed dollar amount.
   */
  fixedUSD: null,

  /* Used when the live exchange rate can't be loaded (1 INR in USD). */
  fallbackInrToUsd: 0.0113,

  /* Free, no-key exchange-rate API. Response must contain rates.USD. */
  rateApi: "https://open.er-api.com/v6/latest/INR",

  /* Visitors in these time zones see ₹ INR; everyone else sees $ USD. */
  indiaTimeZones: ["Asia/Kolkata", "Asia/Calcutta"],

  /*
   * Payment links (Razorpay, Cashfree, Instamojo, Gumroad, Lemon Squeezy…).
   * Leave empty until the product is ready — "Buy" then shows a
   * "checkout opening soon" sheet. If only one link is set, it is used
   * for both currencies.
   */
  checkoutUrl: {
    INR: "",
    USD: "",
  },

  /*
   * After payment: how buyers get the pack. Buyers land on download.html
   * (set it as the "redirect after payment" URL in your payment platform).
   *
   *   method: "platform"  The payment platform gives the download link (on its
   *                        confirmation screen and email). Nothing secret is in
   *                        this public code. Use this for the live store.
   *   method: "link"      download.html shows a button to fullPackUrl
   *                        (e.g. a Google Drive link). Anyone who reads this file
   *                        can see that link, so it's not private.
   *   method: "zip"       download.html offers the ZIPs in downloads/
   *                        (built by tools/build_pack.py from pack/).
   */
  delivery: {
    method: "platform",
    platformName: "",  // e.g. "Instamojo"; shown on the thank-you page
    manifest: "downloads/manifest.json",
    fullPackUrl: "",
  },

  /*
   * Test mode: while no payment link is set, the checkout sheet offers a
   * "Test purchase" button that goes straight to the download page.
   * Keep false on the live site.
   */
  testMode: false,

  /* Optional contact links shown in the footer and the checkout sheet. */
  contact: {
    email: "",      // e.g. "hello@yourdomain.com"
    instagram: "",  // e.g. "https://instagram.com/yourhandle"
    whatsapp: "",   // e.g. "https://wa.me/91XXXXXXXXXX"
  },

  /*
   * Sound previews on the page.
   *  - `src`: path or URL to a real preview file (mp3/wav/m4a), e.g. "assets/audio/whoosh.mp3".
   *  - While `src` is empty, a demo sound is generated in the browser (`synth`)
   *    and a small "demo previews" note is shown under the grid.
   *    Available synths: whoosh, impact, riser, glitch, swish, subdrop, pop, click.
   *  - `icon`: wind, burst, rise, glitch, swish, drop, sparkle, tap.
   */
  previews: [
    { name: "Whoosh",           category: "Transitions", synth: "whoosh",  icon: "wind",    src: "" },
    { name: "Cinematic Impact", category: "Impacts",     synth: "impact",  icon: "burst",   src: "" },
    { name: "Tension Riser",    category: "Risers",      synth: "riser",   icon: "rise",    src: "" },
    { name: "Digital Glitch",   category: "Glitches",    synth: "glitch",  icon: "glitch",  src: "" },
    { name: "Quick Swish",      category: "Transitions", synth: "swish",   icon: "swish",   src: "" },
    { name: "Sub Drop",         category: "Bass",        synth: "subdrop", icon: "drop",    src: "" },
    { name: "Text Pop",         category: "Pops",        synth: "pop",     icon: "sparkle", src: "" },
    { name: "UI Tap",           category: "Interface",   synth: "click",   icon: "tap",     src: "" },
  ],
};
