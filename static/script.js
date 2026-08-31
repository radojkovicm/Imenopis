// Serbian Cyrillic -> Latin transliteration, display-layer only. Mirrors
// src/util/transliteration.py exactly (kept in sync by hand) - the API
// always returns the source's original Cyrillic form (§6.1: source_form is
// authoritative), this module only affects what the browser shows.
//
// Persisted per-viewer in localStorage (not sent to the server) so the
// choice survives navigation between pages without a build step or
// server-side templating (§6.2).

const DIGRAPHS = {
  Љ: "Lj", љ: "lj",
  Њ: "Nj", њ: "nj",
  Џ: "Dž", џ: "dž",
};

const SINGLE = {
  А: "A", а: "a", Б: "B", б: "b", В: "V", в: "v", Г: "G", г: "g",
  Д: "D", д: "d", Ђ: "Đ", ђ: "đ", Е: "E", е: "e", Ж: "Ž", ж: "ž",
  З: "Z", з: "z", И: "I", и: "i", Ј: "J", ј: "j", К: "K", к: "k",
  Л: "L", л: "l", М: "M", м: "m", Н: "N", н: "n", О: "O", о: "o",
  П: "P", п: "p", Р: "R", р: "r", С: "S", с: "s", Т: "T", т: "t",
  Ћ: "Ć", ћ: "ć", У: "U", у: "u", Ф: "F", ф: "f", Х: "H", х: "h",
  Ц: "C", ц: "c", Ч: "Č", ч: "č", Ш: "Š", ш: "š",
};

export function cyrillicToLatin(text) {
  if (typeof text !== "string") return text;
  let out = "";
  for (const ch of text) {
    out += DIGRAPHS[ch] ?? SINGLE[ch] ?? ch;
  }
  return out;
}

const STORAGE_KEY = "imenopis-script";

export function getScriptPref() {
  try {
    return localStorage.getItem(STORAGE_KEY) === "latin" ? "latin" : "cyrillic";
  } catch {
    return "cyrillic";
  }
}

export function setScriptPref(pref) {
  try {
    localStorage.setItem(STORAGE_KEY, pref);
  } catch {
    // private browsing / storage blocked - preference just won't persist
  }
}

// Renders text through the current script preference. Use this instead of
// setting .textContent directly anywhere user-facing Cyrillic source data
// is shown, so a single toggle affects the whole page.
export function display(text) {
  return getScriptPref() === "latin" ? cyrillicToLatin(text) : text;
}

// Installs the toggle control into a container element (typically the site
// header) and re-renders the page's text on change by dispatching a custom
// event other scripts can listen for.
export function installScriptToggle(container) {
  const wrap = document.createElement("span");
  wrap.className = "script-toggle";

  const makeButton = (pref, label) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = label;
    btn.dataset.pref = pref;
    btn.addEventListener("click", () => {
      setScriptPref(pref);
      updateActiveState();
      window.dispatchEvent(new CustomEvent("scriptprefchange", { detail: { pref } }));
    });
    return btn;
  };

  const cyrBtn = makeButton("cyrillic", "Ћирилица");
  const latBtn = makeButton("latin", "Latinica");
  wrap.append(cyrBtn, latBtn);
  container.appendChild(wrap);

  function updateActiveState() {
    const current = getScriptPref();
    cyrBtn.classList.toggle("active", current === "cyrillic");
    latBtn.classList.toggle("active", current === "latin");
  }
  updateActiveState();
}
