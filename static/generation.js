import { getGeneration, compareGenerations, getAcrossDecades } from "/static/api.js";
import { renderRankList, renderUnknownNote, isKnown } from "/static/evidence.js";

const yearForm = document.getElementById("year-form");
const yearInput = document.getElementById("year-input");
const yearResult = document.getElementById("year-result");

yearForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const year = parseInt(yearInput.value, 10);
  if (!year) return;
  yearResult.innerHTML = "<p>Tražim…</p>";
  const data = await getGeneration(year);
  renderYearResult(data);
});

function renderYearResult(data) {
  yearResult.innerHTML = "";
  const h2 = document.createElement("h2");
  h2.textContent = `${data.year}.`;
  yearResult.appendChild(h2);

  const cols = document.createElement("div");
  cols.className = "compare-columns";
  cols.style.gridTemplateColumns = "1fr 1fr";

  for (const [label, envelope] of [
    ["Ženska imena", data.female],
    ["Muška imena", data.male],
  ]) {
    const col = document.createElement("div");
    const h4 = document.createElement("h4");
    h4.textContent = label;
    col.appendChild(h4);
    if (isKnown(envelope) && envelope.value.length > 0) {
      renderRankList(col, envelope.value);
    } else {
      renderUnknownNote(col, envelope ? envelope.reason : "scope_not_published");
    }
    cols.appendChild(col);
  }

  yearResult.appendChild(cols);
}

const compareForm = document.getElementById("compare-form");
const yearAInput = document.getElementById("year-a");
const yearBInput = document.getElementById("year-b");
const compareResult = document.getElementById("compare-result");

compareForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const a = parseInt(yearAInput.value, 10);
  const b = parseInt(yearBInput.value, 10);
  if (!a || !b) return;
  compareResult.innerHTML = "<p>Poredim…</p>";
  const data = await compareGenerations(a, b);
  renderCompareResult(data);
});

function renderCompareResult(data) {
  compareResult.innerHTML = "";
  for (const [label, envelope] of [
    ["Ženska imena", data.female],
    ["Muška imena", data.male],
  ]) {
    const section = document.createElement("div");
    const h3 = document.createElement("h3");
    h3.textContent = label;
    section.appendChild(h3);

    if (!envelope || envelope.evidence === "unknown") {
      renderUnknownNote(section, envelope ? envelope.reason : "scope_not_published");
      compareResult.appendChild(section);
      continue;
    }

    const cols = document.createElement("div");
    cols.className = "compare-columns";
    for (const [colLabel, key] of [
      [`Ušlo u top 5 (${data.b})`, "entered"],
      [`Ispalo iz top 5 (${data.b})`, "left"],
      ["U oba perioda", "present_in_both"],
    ]) {
      const col = document.createElement("div");
      const h4 = document.createElement("h4");
      h4.textContent = colLabel;
      col.appendChild(h4);
      const ul = document.createElement("ul");
      const names = envelope.value[key];
      if (names.length === 0) {
        const li = document.createElement("li");
        li.textContent = "—";
        ul.appendChild(li);
      } else {
        for (const name of names) {
          const li = document.createElement("li");
          li.textContent = name;
          ul.appendChild(li);
        }
      }
      col.appendChild(ul);
      cols.appendChild(col);
    }
    section.appendChild(cols);

    const note = document.createElement("p");
    note.className = "source-note";
    note.textContent =
      "Zasnovano na prvih pet imena po godini rođenja — izlazak iz ove liste ne znači da je ime nestalo, samo da nije bilo među pet najčešćih.";
    section.appendChild(note);

    compareResult.appendChild(section);
  }
}

const decadesForm = document.getElementById("decades-form");
const decadesYearInput = document.getElementById("decades-year");
const decadesResult = document.getElementById("decades-result");

decadesForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const year = parseInt(decadesYearInput.value, 10);
  if (!year) return;
  decadesResult.innerHTML = "<p>Tražim…</p>";
  const data = await getAcrossDecades(year);
  renderDecadesResult(data);
});

function renderDecadesResult(data) {
  decadesResult.innerHTML = "";
  const cols = document.createElement("div");
  cols.className = "compare-columns";
  cols.style.gridTemplateColumns = "1fr 1fr";

  for (const [label, entries] of [
    ["Da si devojčica", data.female],
    ["Da si dečak", data.male],
  ]) {
    const col = document.createElement("div");
    const h4 = document.createElement("h4");
    h4.textContent = label;
    col.appendChild(h4);
    const ul = document.createElement("ul");
    for (const e of entries) {
      const li = document.createElement("li");
      const nameKnown = e.name.evidence !== "unknown";
      li.textContent = nameKnown ? `${e.year}. — ${e.name.value}` : `${e.year}. — nema podataka`;
      ul.appendChild(li);
    }
    col.appendChild(ul);
    cols.appendChild(col);
  }

  decadesResult.appendChild(cols);

  const note = document.createElement("p");
  note.className = "source-note";
  note.textContent = "Najčešće (#1) ime te godine, na republičkom nivou, unazad po deceniji.";
  decadesResult.appendChild(note);
}
