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

  async function init() {
    if (new URLSearchParams(location.search).has("test")) $("[data-test-banner]").hidden = false;
    $$("[data-year]").forEach((el) => { el.textContent = String(new Date().getFullYear()); });

    const contact = C.contact || {};
    const help = $("[data-contact-help]");
    if (help && contact.instagram) {
      help.innerHTML = `Message <a href="${escapeHTML(contact.instagram)}" target="_blank" rel="noopener">Aminur Rex on Instagram</a>.`;
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
