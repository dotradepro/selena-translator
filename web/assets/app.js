"use strict";

const I18N = {
  en: {
    "brand": "Selena Translator",
    "tab.translate": "Translate",
    "tab.helsinki": "Helsinki Converter",
    "source": "Source",
    "target": "Target",
    "translate.btn": "Translate",
    "packs.manage": "Manage language packs",
    "packs.title": "Argos language packs",
    "packs.install": "Install",
    "packs.remove": "Remove",
    "packs.installed": "Installed",
    "refresh": "Refresh",
    "from": "From",
    "to": "To",
    "action": "Action",
    "source.placeholder": "Enter text to translate",
    "helsinki.info":
      "Convert Helsinki-NLP opus-mt models from HuggingFace into SelenaCore-compatible CTranslate2 archives.",
    "helsinki.catalog": "Catalog",
    "helsinki.model": "HuggingFace model ID",
    "helsinki.direction": "Direction",
    "helsinki.token": "Language token",
    "helsinki.quant": "Quantization",
    "helsinki.convert": "Convert",
    "helsinki.log": "Job log",
    "helsinki.download": "Download archive",
  },
  uk: {
    "brand": "Selena Translator",
    "tab.translate": "Переклад",
    "tab.helsinki": "Конвертер Helsinki",
    "source": "Джерело",
    "target": "Ціль",
    "translate.btn": "Перекласти",
    "packs.manage": "Керувати мовними пакетами",
    "packs.title": "Мовні пакети Argos",
    "packs.install": "Встановити",
    "packs.remove": "Видалити",
    "packs.installed": "Встановлено",
    "refresh": "Оновити",
    "from": "З мови",
    "to": "На мову",
    "action": "Дія",
    "source.placeholder": "Введіть текст для перекладу",
    "helsinki.info":
      "Конвертація моделей Helsinki-NLP opus-mt з HuggingFace у сумісні з SelenaCore архіви CTranslate2.",
    "helsinki.catalog": "Каталог",
    "helsinki.model": "HuggingFace ID моделі",
    "helsinki.direction": "Напрям",
    "helsinki.token": "Мовний токен",
    "helsinki.quant": "Квантизація",
    "helsinki.convert": "Конвертувати",
    "helsinki.log": "Журнал завдання",
    "helsinki.download": "Завантажити архів",
  },
};

const store = {
  lang: localStorage.getItem("lang") || "uk",
  theme: localStorage.getItem("theme") || "light",
};

function applyTheme(theme) {
  document.documentElement.setAttribute("data-bs-theme", theme);
  document.getElementById("theme-icon").textContent = theme === "dark" ? "☀️" : "🌙";
  localStorage.setItem("theme", theme);
  store.theme = theme;
}

function applyLang(lang) {
  const dict = I18N[lang] || I18N.en;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) el.textContent = dict[key];
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (dict[key]) el.setAttribute("placeholder", dict[key]);
  });
  document.querySelectorAll("[data-lang]").forEach((btn) => {
    btn.classList.toggle("active", btn.getAttribute("data-lang") === lang);
  });
  localStorage.setItem("lang", lang);
  store.lang = lang;
}

function t(key) {
  return (I18N[store.lang] || I18N.en)[key] || key;
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText} ${body}`);
  }
  return res.json();
}

async function loadLanguages() {
  const data = await api("/api/languages");
  const langs = data.languages || [];
  const src = document.getElementById("src-lang");
  const tgt = document.getElementById("tgt-lang");
  src.innerHTML = "";
  tgt.innerHTML = "";
  for (const lang of langs) {
    const option = (el) => {
      const o = document.createElement("option");
      o.value = lang.code;
      o.textContent = `${lang.name} (${lang.code})`;
      el.appendChild(o);
    };
    option(src);
    option(tgt);
  }
  if (langs.length >= 2) {
    src.value = langs.find((l) => l.code === "en")?.code || langs[0].code;
    tgt.value = langs.find((l) => l.code === "uk")?.code || langs[1].code;
  }
}

async function doTranslate() {
  const src = document.getElementById("src-lang").value;
  const tgt = document.getElementById("tgt-lang").value;
  const text = document.getElementById("src-text").value;
  const status = document.getElementById("translate-status");
  const output = document.getElementById("tgt-text");
  if (!text.trim()) {
    output.value = "";
    return;
  }
  status.textContent = "…";
  try {
    const res = await api("/api/translate", {
      method: "POST",
      body: JSON.stringify({ text, from: src, to: tgt }),
    });
    output.value = res.translation;
    status.textContent = "";
  } catch (err) {
    status.textContent = String(err.message || err);
  }
}

function swap() {
  const src = document.getElementById("src-lang");
  const tgt = document.getElementById("tgt-lang");
  [src.value, tgt.value] = [tgt.value, src.value];
  const sText = document.getElementById("src-text");
  const tText = document.getElementById("tgt-text");
  [sText.value, tText.value] = [tText.value, sText.value];
}

async function refreshPacks() {
  const body = document.getElementById("packs-body");
  const count = document.getElementById("packs-count");
  body.innerHTML = `<tr><td colspan="3">…</td></tr>`;
  try {
    const packs = await api("/api/packages/available");
    body.innerHTML = "";
    let installed = 0;
    for (const p of packs) {
      if (p.installed) installed++;
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${p.from_name} <span class="text-body-secondary small">(${p.from_code})</span></td>
        <td>${p.to_name} <span class="text-body-secondary small">(${p.to_code})</span></td>
        <td class="text-end"></td>`;
      const cell = tr.lastElementChild;
      if (p.installed) {
        const btn = document.createElement("button");
        btn.className = "btn btn-sm btn-outline-danger";
        btn.textContent = t("packs.remove");
        btn.onclick = async () => {
          btn.disabled = true;
          await fetch(`/api/packages/${p.from_code}-${p.to_code}`, {
            method: "DELETE",
          });
          await refreshPacks();
          await loadLanguages();
        };
        cell.appendChild(btn);
      } else {
        const btn = document.createElement("button");
        btn.className = "btn btn-sm btn-outline-primary";
        btn.textContent = t("packs.install");
        btn.onclick = async () => {
          btn.disabled = true;
          btn.textContent = "…";
          try {
            await api("/api/packages/install", {
              method: "POST",
              body: JSON.stringify({ from: p.from_code, to: p.to_code }),
            });
            await refreshPacks();
            await loadLanguages();
          } catch (e) {
            btn.textContent = String(e.message || e);
          }
        };
        cell.appendChild(btn);
      }
      body.appendChild(tr);
    }
    count.textContent = `${installed} / ${packs.length} ${t("packs.installed").toLowerCase()}`;
  } catch (err) {
    body.innerHTML = `<tr><td colspan="3" class="text-danger">${err.message}</td></tr>`;
  }
}

async function loadCatalog() {
  try {
    const cat = await api("/api/helsinki/catalog");
    const sel = document.getElementById("h-catalog");
    for (const entry of cat) {
      const o = document.createElement("option");
      o.value = JSON.stringify(entry);
      o.textContent = `${entry.direction} — ${entry.description}`;
      sel.appendChild(o);
    }
    sel.addEventListener("change", () => {
      if (!sel.value) return;
      const e = JSON.parse(sel.value);
      document.getElementById("h-model").value = e.model_id;
      document.getElementById("h-direction").value = e.direction;
      document.getElementById("h-token").value = e.language_token || "";
    });
  } catch (err) {
    console.error(err);
  }
}

async function startConvert() {
  const model_id = document.getElementById("h-model").value.trim();
  const direction = document.getElementById("h-direction").value.trim();
  const language_token = document.getElementById("h-token").value.trim();
  const quantization = document.getElementById("h-quant").value;
  const logBox = document.getElementById("h-log");
  const progress = document.getElementById("h-progress");
  const dl = document.getElementById("h-download");
  dl.classList.add("d-none");
  logBox.textContent = "";
  if (!model_id || !direction) {
    logBox.textContent = "model_id and direction required";
    return;
  }
  progress.textContent = "queued";
  progress.className = "badge text-bg-secondary me-2";
  const res = await api("/api/helsinki/convert", {
    method: "POST",
    body: JSON.stringify({ model_id, direction, language_token, quantization }),
  });
  pollJob(res.job_id);
}

async function pollJob(jid) {
  const logBox = document.getElementById("h-log");
  const progress = document.getElementById("h-progress");
  const dl = document.getElementById("h-download");
  while (true) {
    const job = await api(`/api/helsinki/jobs/${jid}`);
    logBox.textContent = job.log.join("\n");
    logBox.scrollTop = logBox.scrollHeight;
    progress.textContent = `${job.state} · ${job.progress}%`;
    progress.className =
      "badge me-2 " +
      (job.state === "done"
        ? "text-bg-success"
        : job.state === "error"
        ? "text-bg-danger"
        : "text-bg-info");
    if (job.state === "done") {
      dl.href = `/api/helsinki/download/${jid}`;
      dl.classList.remove("d-none");
      return;
    }
    if (job.state === "error") return;
    await new Promise((r) => setTimeout(r, 1500));
  }
}

document.addEventListener("DOMContentLoaded", () => {
  applyTheme(store.theme);
  applyLang(store.lang);
  document
    .getElementById("theme-toggle")
    .addEventListener("click", () => applyTheme(store.theme === "dark" ? "light" : "dark"));
  document
    .querySelectorAll("[data-lang]")
    .forEach((btn) => btn.addEventListener("click", () => applyLang(btn.getAttribute("data-lang"))));
  document.getElementById("translate-btn").addEventListener("click", doTranslate);
  document.getElementById("swap-btn").addEventListener("click", swap);
  document.getElementById("packs-refresh").addEventListener("click", refreshPacks);
  document
    .getElementById("packs-modal")
    .addEventListener("shown.bs.modal", refreshPacks);
  document.getElementById("h-convert").addEventListener("click", startConvert);

  loadLanguages();
  loadCatalog();
});
