import { getNewborn } from "/static/api.js";
import { renderRankList, renderUnknownNote, isKnown } from "/static/evidence.js";

const form = document.getElementById("newborn-form");
const yearSelect = document.getElementById("year-select");
const districtSelect = document.getElementById("district-select");
const resultEl = document.getElementById("newborn-result");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  await load();
});

districtSelect.addEventListener("change", load);

async function load() {
  const year = parseInt(yearSelect.value, 10);
  const district = districtSelect.value || undefined;
  resultEl.innerHTML = "<p>Tražim…</p>";
  const data = await getNewborn(year, { district });
  render(data);
}

function render(data) {
  resultEl.innerHTML = "";
  const cols = document.createElement("div");
  cols.className = "compare-columns";
  cols.style.gridTemplateColumns = "1fr 1fr";

  for (const [label, envelope] of [
    ["Devojčice", data.female],
    ["Dečaci", data.male],
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

  resultEl.appendChild(cols);
}

load();
