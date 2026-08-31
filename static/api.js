// Thin fetch wrapper. No build step, plain ES module (PROJECT.md §6.2).

const BASE = "/api";

async function getJSON(path) {
  const res = await fetch(BASE + path);
  if (!res.ok) {
    throw new Error(`Request failed: ${path} (${res.status})`);
  }
  return res.json();
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

export function getNewborn(year, { gender, district } = {}) {
  const params = new URLSearchParams();
  if (gender) params.set("gender", gender);
  if (district) params.set("district", district);
  const qs = params.toString();
  return getJSON(`/newborn/${year}${qs ? "?" + qs : ""}`);
}
