// Ported from mexicat/pdoom-video (MIT, see LICENSE-pdoom-video.txt) and adapted for One Prompt.
import { hexToLinear } from './util.js';

// The whole video lives in a restrained palette: ink, bone, and one signal colour.
// One rare accent (acid): the violet of "purple words".
export const HEX = {
  ink: '#0A0A0B', // background black (slightly warm)
  ink2: '#151517', // raised black (panels, paper-in-the-dark)
  graphite: '#5E5B57', // dim lines, secondary text
  ash: '#9C978F', // mid grey
  bone: '#EEE9DF', // paper white, primary text
  signal: '#FF5A1F', // the caret: the one thing alive
  ember: '#FF9A4D', // hot cores
  blood: '#B8260E', // deep orange shadow
  acid: '#8B5CFF', // violet: only for "purple words" (the key keeps the reference's name)
};

/** Linear RGB triplets for GL uniforms. */
export const LIN = Object.fromEntries(
  Object.entries(HEX).map(([k, v]) => [k, hexToLinear(v)]),
);

/** CSS rgba() for Canvas2D. */
export function rgba(key, a = 1) {
  const hex = (HEX)[key] ?? key;
  const n = parseInt(hex.replace('#', ''), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}
