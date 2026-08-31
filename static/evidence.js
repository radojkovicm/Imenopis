// Rendering helpers for the §4 evidence envelope. The one rule that matters
// most here: an envelope with evidence:"unknown" must never be turned into a
// characterisation of the name (§4.4) - no "retk-", "čest-", "popular",
// "koncentr-", no "%". This module is the single choke point every page goes
// through to render an envelope, specifically so that rule only has to be
// obeyed in one place.

const REASON_TEXT = {
  source_is_top10_only:
    "Zvanična statistika objavljuje samo prvih deset imena po opštini — sve ispod desetog mesta je nevidljivo.",
  source_is_top5_only:
    "Za ovu godinu rođenja zvanična statistika objavljuje samo prvih pet imena.",
  scope_not_published: "Ovaj podatak nije objavljen za traženi opseg.",
  source_has_no_counts: "Izvor ne objavljuje apsolutne brojeve, samo rang.",
  below_confidentiality_threshold: "Podatak je sakriven zbog statističke poverljivosti.",
};

export function reasonText(reason) {
  return REASON_TEXT[reason] || "Podatak nije dostupan iz izvora.";
}

export function isKnown(envelope) {
  return envelope && envelope.evidence !== "unknown" && envelope.value != null;
}

// Renders a list of {rank, name} into an <ol>/<ul>-free rank list. Caller
// supplies the container element; this only builds children.
export function renderRankList(container, items) {
  container.innerHTML = "";
  const ul = document.createElement("ul");
  ul.className = "rank-list";
  for (const item of items) {
    const li = document.createElement("li");
    const rankSpan = document.createElement("span");
    rankSpan.className = "rank";
    rankSpan.textContent = item.rank != null ? `#${item.rank}` : "—";
    const nameSpan = document.createElement("span");
    nameSpan.textContent = item.name;
    li.append(rankSpan, nameSpan);
    ul.appendChild(li);
  }
  container.appendChild(ul);
}

export function renderUnknownNote(container, reason) {
  const p = document.createElement("p");
  p.className = "source-note";
  p.textContent = reasonText(reason);
  container.appendChild(p);
}
