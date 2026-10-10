// Asset loading. Paths are relative to the film's folder (the one with film.html), wherever the page that
// imports this sits.
const ROOT = new URL('../../', import.meta.url);

export async function loadBytes(path) {
  const res = await fetch(new URL(path, ROOT));
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.arrayBuffer();
}
export const loadText = (path) => loadBytes(path).then((b) => new TextDecoder().decode(b));
export const loadJSON = (path) => loadText(path).then((s) => JSON.parse(s));
