// Real glyph outlines for type built as geometry: Archivo Black as a three.js typeface (converted from the
// font with fontTools, in font-archivo-black.js). The marquee's letter board and the premiere's title use it.
import { FontLoader } from 'three/addons/loaders/FontLoader.js';
import archivoBlack from './font-archivo-black.js';

const RAW = { block: archivoBlack };
const FONTS = new Map();
export function font(name) {
  let f = FONTS.get(name);
  if (!f) { f = new FontLoader().parse(RAW[name]); FONTS.set(name, f); }
  return f;
}
