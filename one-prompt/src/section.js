// One section of the film as a page: a canvas, a WebGL renderer, and the engine (px/engine.js) playing the
// section's plates (plates/timeline.js). The page's t is its own time from 0; the song's time is the
// section's start plus t, so the clip sits at that start in film.html, where the song is.
import * as THREE from 'three';
import { Engine } from './px/engine.js';
import { Lyrics } from './px/lyrics.js';
import { W, H, SCALE } from './px/gl.js';
import { WORDS, LINES } from './lyrics.js';
import { makeTimeline, sectionSpan } from './plates/timeline.js';

export function section(name) {
  const { start, end } = sectionSpan(name);
  const canvas = document.createElement('canvas');
  canvas.style.cssText = 'display: block; width: 100vw; height: 100vh';
  document.body.append(canvas);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(SCALE);
  renderer.setSize(W, H, false);
  const engine = new Engine(renderer, makeTimeline(name), () => Lyrics.fromTables(WORDS, LINES));

  /** draw song time t: one sample per frame (a render's motion blur is the host's: `openfilm render --blur`) */
  const draw = (t) => {
    engine.lastT = -1; // every frame is drawn as if seeked to: nothing carries over from the frame before
    engine.render(Math.min(Math.max(t, start), end - 1e-3), 1 / 60, true, 1);
  };

  window.film = {
    duration: Math.round((end - start) * 1000) / 1000,
    // fonts, the song's analysis and every plate's own set-up; then a frame at each plate's start, so its
    // shaders are compiled before the first frame is asked for
    ready: engine.init().then(() => {
      if (engine.errors.length) throw new Error(engine.errors.join('\n'));
      for (const e of engine.timeline) draw(e.start);
    }),
    frame(t) { draw(start + t); },
  };

  // opened on its own (not by a film host), the page plays itself, silent
  if (!window.filmHost) {
    window.film.ready.then(() => {
      const t0 = performance.now();
      const loop = () => { window.film.frame(((performance.now() - t0) / 1000) % window.film.duration); requestAnimationFrame(loop); };
      loop();
    });
  }
}
