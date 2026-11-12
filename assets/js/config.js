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
   * After payment. In your payment provider, set the "success / redirect URL" to the
   * download page, e.g. https://your-site.com/download.html
   * The page lists the pack from downloads/manifest.json (built by tools/build_pack.py).
   * To host the big full-pack zip elsewhere (Google Drive, Dropbox), paste its link
   * in fullPackUrl; the category downloads keep using the files in downloads/.
   */
  delivery: {
    manifest: "downloads/manifest.json",
    // The pack in Google Drive (folder shared as "Anyone with the link").
    fullPackUrl: "https://drive.google.com/drive/folders/1mwBhxkkKt74TQOyBpvkO95EfA0b6Fk-p?usp=sharing",
  },

  /*
   * Test mode: while no payment link is set, the checkout sheet offers a
   * "Test purchase" button that goes straight to the download page.
   * Set to false before launch.
   */
  testMode: true,

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
