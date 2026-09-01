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

// §16.2/§16.3 rule 2: a historical_confidence of "D" must never be
// presented as an attested fact. This is the one place that copy is
// generated, so the rule only has to be obeyed here - every caller that
// renders a historical attestation should go through this function rather
// than writing its own "potvrđeno"/"najčešće" string.
const CONFIDENCE_TEXT = {
  A: "statistički dokazano",
  B: "među najčešće zabeleženim (kvantitativni istorijski izvor)",
  C: "istorijski potvrđeno",
  D: "pretpostavljeno / rekonstruisano — nije potvrđeno",
};

const CONFIDENCE_BADGE = {
  A: "A — dokazano",
  B: "B — zabeleženo",
  C: "C — potvrđeno",
  D: "D — pretpostavljeno",
};

export function confidenceText(level) {
  return CONFIDENCE_TEXT[level] || "nepoznat nivo pouzdanosti";
}

export function confidenceBadge(level) {
  return CONFIDENCE_BADGE[level] || level;
}
