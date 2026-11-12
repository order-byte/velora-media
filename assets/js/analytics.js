/* ==========================================================================
   Analytics — Microsoft Clarity (visitor counts, heatmaps, session replays).
   The project ID lives in config.js (analytics.clarityId); leave it empty to turn analytics off.
   Other scripts record moments with window.track("event_name").
   ========================================================================== */
(() => {
  "use strict";

  const id = ((window.STORE_CONFIG || {}).analytics || {}).clarityId || "";

  // Queue calls until Clarity's script has loaded (same stub as Clarity's own snippet).
  window.clarity = window.clarity || function () {
    (window.clarity.q = window.clarity.q || []).push(arguments);
  };

  /** Record a named moment, e.g. track("buy_click"). Safe to call even when analytics is off. */
  window.track = (name, tags) => {
    if (!id) return;
    try {
      if (tags) Object.keys(tags).forEach((k) => window.clarity("set", k, String(tags[k])));
      window.clarity("event", name);
    } catch { /* analytics must never break the page */ }
  };

  if (!id) return;
  const script = document.createElement("script");
  script.async = true;
  script.src = `https://www.clarity.ms/tag/${encodeURIComponent(id)}`;
  document.head.appendChild(script);
})();
