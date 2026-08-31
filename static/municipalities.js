import { listMunicipalities } from "/static/api.js";
import { installScriptToggle } from "/static/script.js";

installScriptToggle(document.getElementById("site-header"));
window.addEventListener("scriptprefchange", load);

// Mirrors src/util/normalize.py's diacritic fold (Latin side only - this
// page's filter box is typed in Latin script even though the data is
// Cyrillic, matched against name_slug). Kept in sync by hand; if
// normalize.py's fold table changes, update this too.
const DIACRITIC_FOLD = { š: "s", č: "c", ć: "c", ž: "z", đ: "dj" };
function foldLatin(text) {
  return text
    .toLowerCase()
    .replace(/[ščćžđ]/g, (ch) => DIACRITIC_FOLD[ch]);
}

const listEl = document.getElementById("municipality-list");
const filterInput = document.getElementById("filter-input");

let allMunicipalities = [];

async function load() {
  allMunicipalities = await listMunicipalities();
  render(allMunicipalities);
}

function render(items) {
  listEl.innerHTML = "";
  for (const m of items) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = `/static/municipality.html?slug=${encodeURIComponent(m.slug)}`;
    a.textContent = m.name;
    li.appendChild(a);
    listEl.appendChild(li);
  }
}

filterInput.addEventListener("input", () => {
  const raw = filterInput.value.trim().toLowerCase();
  if (!raw) {
    render(allMunicipalities);
    return;
  }
  // Filter against name_slug (Latin/ASCII, diacritic-folded, per §6.1's
  // search_key convention) as well as the raw Cyrillic name - a
  // Serbian-keyboard user might type either script, or Latin with
  // diacritics (Šabac) that don't literally appear in the slug (sabac).
  const foldedQuery = foldLatin(raw);
  render(
    allMunicipalities.filter(
      (m) => m.name.toLowerCase().includes(raw) || m.slug.includes(foldedQuery)
    )
  );
});

load();
