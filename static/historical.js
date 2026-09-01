import { getHistorical, listHistorical } from "/static/api.js";
import { confidenceBadge, confidenceText } from "/static/evidence.js";
import { installScriptToggle } from "/static/script.js";

installScriptToggle(document.getElementById("site-header"));

const nameForm = document.getElementById("hist-name-form");
const nameInput = document.getElementById("hist-name-input");
const nameResult = document.getElementById("hist-name-result");

let lastQuery = null;

async function searchName(query) {
  if (!query) return;
  lastQuery = query;
  nameResult.innerHTML = "<p>Tražim…</p>";
  const data = await getHistorical(query);
  renderNameResult(data);
}

nameForm.addEventListener("submit", (e) => {
  e.preventDefault();
  searchName(nameInput.value.trim());
});

function renderNameResult(data) {
  nameResult.innerHTML = "";

  if (!data.matches || data.matches.length === 0) {
    const p = document.createElement("p");
    p.className = "source-note";
    p.textContent = "Ovo ime nema zabeleženu potvrdu u istorijskom korpusu — to ne znači da ime ne postoji, samo da nije (još) unešeno.";
    nameResult.appendChild(p);
    return;
  }

  if (data.split_notice) {
    const notice = document.createElement("div");
    notice.className = "split-notice";
    notice.textContent = data.split_notice;
    nameResult.appendChild(notice);
  }

  for (const block of data.matches) {
    nameResult.appendChild(renderBlock(block));
  }
}

function renderBlock(block) {
  const wrap = document.createElement("div");
  wrap.className = "name-block";

  const h3 = document.createElement("h3");
  h3.textContent = `${block.source_form} (${block.gender === "F" ? "žensko" : "muško"} ime)`;
  wrap.appendChild(h3);

  for (const a of block.attestations) {
    wrap.appendChild(renderAttestation(a));
  }

  return wrap;
}

function renderAttestation(a) {
  const box = document.createElement("div");
  box.style.borderTop = "1px solid var(--border)";
  box.style.paddingTop = "0.75rem";
  box.style.marginTop = "0.75rem";

  const badge = document.createElement("span");
  badge.className = "badge";
  badge.textContent = confidenceBadge(a.historical_confidence);
  box.appendChild(badge);

  const period = document.createElement("p");
  const span = a.value.period_start != null
    ? (a.value.period_start === a.value.period_end ? `${a.value.period_start}.` : `${a.value.period_start}–${a.value.period_end}.`)
    : "period nepoznat";
  const region = a.value.region ? ` — ${a.value.region}` : "";
  period.textContent = `${span}${region}`;
  box.appendChild(period);

  // §16.3 rule 2: the confidence-level explanation is always shown next to
  // the claim, never left implicit - especially important for D-level rows.
  const confidenceP = document.createElement("p");
  confidenceP.className = "source-note";
  confidenceP.textContent = confidenceText(a.historical_confidence);
  box.appendChild(confidenceP);

  if (a.value.frequency_level) {
    const freqP = document.createElement("p");
    freqP.textContent = `Učestalost u izvoru: ${a.value.frequency_level}`;
    box.appendChild(freqP);
  }

  const citation = document.createElement("p");
  citation.className = "source-note";
  citation.textContent = `Izvor: ${a.citation_note}`;
  box.appendChild(citation);

  return box;
}

// Filter panel
const filterForm = document.getElementById("hist-filter-form");
const nameTypeSelect = document.getElementById("hist-name-type");
const genderSelect = document.getElementById("hist-gender");
const filterResult = document.getElementById("hist-filter-result");

async function loadFilter() {
  filterResult.innerHTML = "<p>Tražim…</p>";
  const data = await listHistorical({
    nameType: nameTypeSelect.value || undefined,
    gender: genderSelect.value || undefined,
  });
  renderFilterResult(data);
}

filterForm.addEventListener("submit", (e) => {
  e.preventDefault();
  loadFilter();
});

function renderFilterResult(data) {
  filterResult.innerHTML = "";
  if (!data.results || data.results.length === 0) {
    const p = document.createElement("p");
    p.className = "source-note";
    p.textContent = "Nema zapisa za izabrani filter.";
    filterResult.appendChild(p);
    return;
  }
  const ul = document.createElement("ul");
  ul.className = "rank-list";
  for (const r of data.results) {
    const li = document.createElement("li");
    const badge = document.createElement("span");
    badge.className = "rank";
    badge.textContent = r.attestation.historical_confidence;
    const nameSpan = document.createElement("span");
    const period = r.attestation.value.period_start != null
      ? `${r.attestation.value.period_start}–${r.attestation.value.period_end}`
      : "";
    nameSpan.textContent = `${r.source_form} (${r.gender === "F" ? "žensko" : "muško"}) — ${period} — ${confidenceBadge(r.attestation.historical_confidence)}`;
    li.append(badge, nameSpan);
    ul.appendChild(li);
  }
  filterResult.appendChild(ul);
}

window.addEventListener("scriptprefchange", () => {
  if (lastQuery) searchName(lastQuery);
  loadFilter();
});

// Pre-fill from ?q= if arriving from the name page (§16.5 cross-link)
const params = new URLSearchParams(window.location.search);
const initialQuery = params.get("q");
if (initialQuery) {
  nameInput.value = initialQuery;
  searchName(initialQuery);
}

loadFilter();
