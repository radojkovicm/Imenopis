import { getMunicipality } from "/static/api.js";
import { isKnown } from "/static/evidence.js";

const titleEl = document.getElementById("muni-title");
const resultEl = document.getElementById("muni-result");

const params = new URLSearchParams(window.location.search);
const slug = params.get("slug");

let data = null;

async function load() {
  if (!slug) {
    resultEl.innerHTML = "<p>Nije izabrana opština.</p>";
    return;
  }
  resultEl.innerHTML = "<p>Tražim…</p>";
  data = await getMunicipality(slug);
  titleEl.textContent = data.name;
  renderControls();
}

function renderControls() {
  resultEl.innerHTML = "";

  // §7.6: a 9-step control over cohorts (never labeled with years - the
  // cohort buckets are unequal-length, per §5.4, so "1 of 9" would be
  // misleading; the cohort label itself is the only honest axis label).
  const controls = document.createElement("div");
  controls.className = "search-form";

  const genderSelect = document.createElement("select");
  for (const [value, label] of [
    ["F", "Ženska imena"],
    ["M", "Muška imena"],
  ]) {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = label;
    genderSelect.appendChild(opt);
  }

  const cohortSelect = document.createElement("select");
  const femaleCohorts = data.cohorts.female;
  femaleCohorts.forEach((c, idx) => {
    const opt = document.createElement("option");
    opt.value = String(idx);
    opt.textContent = c.cohort;
    cohortSelect.appendChild(opt);
  });
  cohortSelect.value = String(femaleCohorts.length - 1); // default: most recent cohort

  controls.append(genderSelect, cohortSelect);
  resultEl.appendChild(controls);

  const tableContainer = document.createElement("div");
  resultEl.appendChild(tableContainer);

  function update() {
    const gender = genderSelect.value;
    const idx = parseInt(cohortSelect.value, 10);
    const key = gender === "F" ? "female" : "male";
    renderCohortTable(tableContainer, data.cohorts[key][idx]);
  }

  genderSelect.addEventListener("change", update);
  cohortSelect.addEventListener("change", update);
  update();
}

function renderCohortTable(container, cohortBlock) {
  container.innerHTML = "";

  const h3 = document.createElement("h3");
  h3.textContent = `Rođeni ${cohortBlock.cohort}`;
  container.appendChild(h3);

  const top10 = cohortBlock.top10;
  if (!isKnown(top10) || top10.value.length === 0) {
    const p = document.createElement("p");
    p.className = "source-note";
    p.textContent = "Nema podataka za ovu generaciju.";
    container.appendChild(p);
    return;
  }

  const table = document.createElement("table");
  table.className = "limits-table";
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const text of ["Rang", "Ime", "Nacionalni rang"]) {
    const th = document.createElement("th");
    th.textContent = text;
    headRow.appendChild(th);
  }
  thead.appendChild(headRow);
  table.appendChild(thead);
  const tbody = document.createElement("tbody");
  for (const entry of top10.value) {
    const tr = document.createElement("tr");
    const national = entry.national;
    const nationalText = isKnown(national) ? `#${national.value}` : "nije u nacionalnom top 10";
    for (const text of [`#${entry.rank}`, entry.name, nationalText]) {
      const td = document.createElement("td");
      td.textContent = text;
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  container.appendChild(table);
}

load();
