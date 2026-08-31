// Thin fetch wrapper. No build step, plain ES module (PROJECT.md §6.2).

import { getScriptPref, cyrillicToLatin } from "/static/script.js";

const BASE = "/api";

// Every response is transliterated to Latin here, once, right after
// fetching - if the viewer's stored preference is "latin" - rather than
// threading a display() call through every place a page renders a string.
// Applies to every string value in the payload recursively (names,
// municipality labels, etc.) - the API itself always returns the source's
// original Cyrillic form (§6.1: source_form is authoritative), this is a
// display-layer transform on the client's own copy of the response.
function transliterateDeep(value) {
  if (typeof value === "string") return cyrillicToLatin(value);
  if (Array.isArray(value)) return value.map(transliterateDeep);
  if (value && typeof value === "object") {
    const out = {};
    for (const [k, v] of Object.entries(value)) out[k] = transliterateDeep(v);
    return out;
  }
  return value;
}

async function getJSON(path) {
  const res = await fetch(BASE + path);
  if (!res.ok) {
    throw new Error(`Request failed: ${path} (${res.status})`);
  }
  const data = await res.json();
  return getScriptPref() === "latin" ? transliterateDeep(data) : data;
}

export function suggest(q) {
  return getJSON(`/suggest?q=${encodeURIComponent(q)}`);
}

export function getName(searchKey, gender) {
  const qs = gender ? `?gender=${gender}` : "";
  return getJSON(`/name/${encodeURIComponent(searchKey)}${qs}`);
}

export function getGeneration(year) {
  return getJSON(`/generation/${year}`);
}

export function compareGenerations(a, b) {
  return getJSON(`/generation/compare?a=${a}&b=${b}`);
}

export function getAcrossDecades(year) {
  return getJSON(`/generation/across-decades?year=${year}`);
}

export function listMunicipalities() {
  return getJSON("/municipality");
}

export function getMunicipality(slug, gender) {
  const qs = gender ? `?gender=${gender}` : "";
  return getJSON(`/municipality/${encodeURIComponent(slug)}${qs}`);
}

export function getCohortDeviation(cohortId, gender) {
  const qs = gender ? `?gender=${gender}` : "";
  return getJSON(`/cohort/${cohortId}${qs}`);
}

export function getNewborn(year, { gender, district } = {}) {
  const params = new URLSearchParams();
  if (gender) params.set("gender", gender);
  if (district) params.set("district", district);
  const qs = params.toString();
  return getJSON(`/newborn/${year}${qs ? "?" + qs : ""}`);
}
