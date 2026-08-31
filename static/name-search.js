import { suggest, getName } from "/static/api.js";
import { renderRankList, renderUnknownNote, isKnown } from "/static/evidence.js";

const form = document.getElementById("name-form");
const input = document.getElementById("name-input");
const suggestionsEl = document.getElementById("suggestions");
const resultEl = document.getElementById("result");

let suggestTimer = null;

input.addEventListener("input", () => {
  clearTimeout(suggestTimer);
  const q = input.value.trim();
  if (q.length < 1) {
    suggestionsEl.innerHTML = "";
    return;
  }
  suggestTimer = setTimeout(async () => {
    const matches = await suggest(q);
    renderSuggestions(matches);
  }, 150);
});

function renderSuggestions(matches) {
  suggestionsEl.innerHTML = "";
  for (const m of matches) {
    const li = document.createElement("li");
    li.textContent = m.display;
    li.addEventListener("click", () => {
      input.value = m.display;
      suggestionsEl.innerHTML = "";
      search(m.search_key);
    });
    suggestionsEl.appendChild(li);
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  suggestionsEl.innerHTML = "";
  search(input.value.trim());
});

async function search(rawQuery) {
  if (!rawQuery) return;
  resultEl.innerHTML = "<p>Tražim…</p>";
  const data = await getName(rawQuery);

  if (!data.matches || data.matches.length === 0) {
    renderEmptyState(rawQuery);
    return;
  }

  resultEl.innerHTML = "";

  if (data.split_notice) {
    const notice = document.createElement("div");
    notice.className = "split-notice";
    notice.textContent = data.split_notice;
    resultEl.appendChild(notice);
  }

  for (const block of data.matches) {
    resultEl.appendChild(renderNameBlock(block));
  }
}

function renderNameBlock(block) {
  const wrap = document.createElement("div");
  wrap.className = "name-block";

  const h3 = document.createElement("h3");
  h3.textContent = `${block.source_form} (${block.gender === "F" ? "žensko" : "muško"} ime)`;
  wrap.appendChild(h3);

  for (const key of block.source_keys) {
    const sourceTag = document.createElement("span");
    sourceTag.className = "badge";
    sourceTag.textContent = key;
    h3.appendChild(sourceTag);
  }

  // "Kada" — national timeline by birth year (§7.1)
  const nat = block.national_timeline_by_year;
  const natHeading = document.createElement("h4");
  natHeading.textContent = "Nacionalni rang po godini rođenja";
  wrap.appendChild(natHeading);
  if (isKnown(nat) && nat.value.length > 0) {
    const list = document.createElement("div");
    renderRankList(
      list,
      nat.value.map((r) => ({ rank: r.rank, name: `rođeni ${r.birth_year}.` }))
    );
    wrap.appendChild(list);
  } else {
    renderUnknownNote(wrap, nat ? nat.reason : "scope_not_published");
  }

  // Newborn appearances (2021-2025, national + district)
  const newborn = block.newborn_timeline;
  const nbHeading = document.createElement("h4");
  nbHeading.textContent = "Novorođena deca 2021–2025";
  wrap.appendChild(nbHeading);
  if (isKnown(newborn) && newborn.value.length > 0) {
    const list = document.createElement("div");
    renderRankList(
      list,
      newborn.value.map((r) => ({
        rank: r.rank,
        name: r.district ? `${r.year}. — ${r.district}` : `${r.year}. — Republika Srbija`,
      }))
    );
    wrap.appendChild(list);
  } else {
    renderUnknownNote(wrap, newborn ? newborn.reason : "scope_not_published");
  }

  // "Gde" — municipality count, best rank, appearances (§7.1)
  const gdeHeading = document.createElement("h4");
  gdeHeading.textContent = "Gde";
  wrap.appendChild(gdeHeading);

  const muniCount = block.municipality_count;
  const bestRank = block.best_rank;
  if (isKnown(muniCount) && isKnown(bestRank)) {
    const p = document.createElement("p");
    p.textContent = `U top 10 u ${muniCount.value} ${muniCount.value === 1 ? "opštini" : "opština"}. Najbolji rezultat: #${bestRank.value.rank} u ${bestRank.value.municipality} (rođeni ${bestRank.value.cohort}).`;
    wrap.appendChild(p);

    const appearances = block.appearances;
    if (isKnown(appearances) && appearances.value.length > 0) {
      const details = document.createElement("details");
      const summary = document.createElement("summary");
      summary.textContent = `Sve opštine (${appearances.value.length} zapisa)`;
      details.appendChild(summary);
      const list = document.createElement("div");
      renderRankList(
        list,
        appearances.value.map((a) => ({
          rank: a.rank,
          name: `${a.municipality} — rođeni ${a.cohort}`,
        }))
      );
      details.appendChild(list);
      wrap.appendChild(details);
    }
  } else {
    renderUnknownNote(wrap, muniCount ? muniCount.reason : "source_is_top10_only");
  }

  // §7.5 persistence — longest consecutive run, expressed as a year span
  // (§5.4: never a count of cohorts/generations).
  const persistHeading = document.createElement("h4");
  persistHeading.textContent = "Najduži period u top listi";
  wrap.appendChild(persistHeading);

  const natPersist = block.national_persistence;
  if (isKnown(natPersist)) {
    const p = document.createElement("p");
    p.textContent = `Nacionalno (top 5): u top listi kod rođenih ${natPersist.value.year_from}–${natPersist.value.year_to}.`;
    wrap.appendChild(p);
  } else {
    renderUnknownNote(wrap, natPersist ? natPersist.reason : "source_is_top5_only");
  }

  const muniPersist = block.municipality_persistence;
  if (isKnown(muniPersist) && muniPersist.value.length > 0) {
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = `Po opštini (top 10, ${muniPersist.value.length} opština)`;
    details.appendChild(summary);
    const ul = document.createElement("ul");
    for (const m of muniPersist.value) {
      const li = document.createElement("li");
      const span = m.year_from != null ? `${m.year_from}–${m.year_to}` : `do ${m.year_to}`;
      li.textContent = `${m.municipality}: rođeni ${span}`;
      ul.appendChild(li);
    }
    details.appendChild(ul);
    wrap.appendChild(details);
  }

  return wrap;
}

function renderEmptyState(query) {
  resultEl.innerHTML = "";
  const box = document.createElement("div");
  box.className = "empty-state";

  const p1 = document.createElement("p");
  const strong = document.createElement("strong");
  strong.textContent = query;
  p1.append(strong, " nije bilo među 10 najčešćih imena ni u jednoj opštini ni u jednoj generaciji.");
  box.appendChild(p1);

  const p2 = document.createElement("p");
  p2.textContent =
    "Zvanična statistika objavljuje samo prvih deset imena po opštini — sve ispod desetog mesta je nevidljivo. Zato ne znamo koliko ljudi nosi ovo ime, samo da nije bilo među najčešćima.";
  box.appendChild(p2);

  const p3 = document.createElement("p");
  const link = document.createElement("a");
  link.href = "/static/generation.html";
  link.textContent = "Evo šta jeste bilo najčešće u istom periodu →";
  p3.appendChild(link);
  box.appendChild(p3);

  resultEl.appendChild(box);
}
