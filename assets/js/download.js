/* ==========================================================================
   Download page — shown to buyers after payment.
   Lists the pack from downloads/manifest.json (built by tools/build_pack.py).
   ========================================================================== */
(() => {
  "use strict";

  const C = window.STORE_CONFIG || {};
  const delivery = Object.assign({ manifest: "downloads/manifest.json", fullPackUrl: "" }, C.delivery);
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const escapeHTML = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const size = (bytes) => {
    if (!bytes && bytes !== 0) return "";
    if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
    if (bytes < 1024 ** 3) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
    return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
  };
  const plural = (n, word, many = `${word}s`) => `${n} ${n === 1 ? word : many}`;
  const isExternal = (url) => /^https?:\/\//i.test(url) && !url.startsWith(location.origin);

  function setFullLink(url) {
    const link = $("[data-full-download]");
    if (!link || !url) return;
    link.href = url;
    if (isExternal(url)) {
      link.removeAttribute("download");
      link.target = "_blank";
      link.rel = "noopener";
    }
  }

  function render(manifest) {
    $$("[data-pack-name]").forEach((el) => { el.textContent = manifest.name; });
    const cats = manifest.categories || [];
    const meta = [plural(manifest.totalFiles, "sound"), plural(cats.length, "category", "categories")];
    if (!delivery.fullPackUrl && manifest.full) meta.push(size(manifest.full.bytes));
    $("[data-pack-meta]").textContent = meta.join(" · ");
    setFullLink(delivery.fullPackUrl || (manifest.full && manifest.full.url));

    $("[data-categories]").innerHTML = cats.map((cat, i) => `
      <li class="dl-cat">
        <details>
          <summary>
            <svg class="dl-cat__folder" aria-hidden="true"><use href="#i-folder"/></svg>
            <span class="dl-cat__text">
              <strong>${escapeHTML(cat.name)}</strong>
              <span>${plural(cat.files.length, "sound")} · ${size(cat.bytes)}</span>
            </span>
            <svg class="dl-cat__chev ico" aria-hidden="true"><use href="#i-chevron"/></svg>
          </summary>
          <ul class="dl-files">
            ${cat.files.map((f) => `
              <li>
                <svg class="ico" aria-hidden="true"><use href="#i-wave"/></svg>
                <span class="dl-files__name">${escapeHTML(f.name)}</span>
                <span class="dl-files__meta">${escapeHTML(f.type)}${f.seconds ? ` · ${f.seconds.toFixed(1)}s` : ""}</span>
              </li>`).join("")}
          </ul>
        </details>
        <a class="dl-cat__btn" href="${escapeHTML(cat.url)}" download data-category-download="${i}" aria-label="Download ${escapeHTML(cat.name)}">
          <svg class="ico" aria-hidden="true"><use href="#i-download"/></svg><span>Download</span>
        </a>
      </li>`).join("");
  }

  function showError() {
    $("[data-error]").hidden = false;
    $("[data-pack-meta]").textContent = "Your full pack is ready below.";
    setFullLink(delivery.fullPackUrl);
  }

  /* The pack lives in Google Drive (or another site): one button that opens it, plus how to save it. */
  function renderExternal(url) {
    setFullLink(url);
    const drive = /drive\.google\.com/i.test(url);
    const where = drive ? "Google Drive" : "a new tab";
    $("[data-full-label]").textContent = drive ? "Open your pack in Google Drive" : "Open your sound pack";
    $("[data-pack-meta]").textContent = `Every sound, sorted into category folders. Opens in ${where}.`;
    $("[data-full-note]").textContent = drive
      ? "On a computer: open the folder, then click Download at the top to save it all as a ZIP. On a phone: open it in a browser and use ⋮ → Download."
      : "Your pack opens in a new tab. Save it from there.";
    const section = $("[data-category-section]");
    if (section) section.hidden = true;
    const step = $("[data-step-get]");
    if (step && drive) {
      step.innerHTML = "<strong>Download the pack.</strong> In Google Drive, choose Download. Drive saves the folders as a ZIP; unzip it on your computer or phone.";
    }
  }

  /* The payment platform hands out the download link; this page only thanks and guides. */
  function renderPlatform() {
    const from = delivery.platformName ? `${delivery.platformName}` : "the payment page";
    $("[data-pack-meta]").textContent = `Your download link is on the payment confirmation screen and in the email from ${from}.`;
    const button = $("[data-full-download]");
    if (button) button.hidden = true;
    $("[data-full-note]").textContent = "Can't find the email? Check Spam and Promotions, or message us with your payment ID and we'll send the link.";
    const section = $("[data-category-section]");
    if (section) section.hidden = true;
    const step = $("[data-step-get]");
    if (step) {
      step.innerHTML = "<strong>Open your download link.</strong> Download the pack from it, then unzip it on your computer or phone.";
    }
  }

  async function init() {
    const isTest = new URLSearchParams(location.search).has("test");
    if (isTest) $("[data-test-banner]").hidden = false;
    if (typeof window.track === "function") window.track("thank_you_page", { test_purchase: isTest });
    $$("[data-year]").forEach((el) => { el.textContent = String(new Date().getFullYear()); });

    const contact = C.contact || {};
    const help = $("[data-contact-help]");
    if (help && contact.instagram) {
      help.innerHTML = `Message <a href="${escapeHTML(contact.instagram)}" target="_blank" rel="noopener">Aminur Rex on Instagram</a>.`;
    }

    const method = delivery.method || (delivery.fullPackUrl ? "link" : "zip");
    if (method === "platform") {
      renderPlatform();
      return;
    }
    if (method === "link" && delivery.fullPackUrl && isExternal(delivery.fullPackUrl)) {
      renderExternal(delivery.fullPackUrl);
      return;
    }

    try {
      const res = await fetch(delivery.manifest, { cache: "no-store" });
      if (!res.ok) throw new Error(`manifest ${res.status}`);
      render(await res.json());
    } catch {
      showError();
    }
  }

  init();
})();
