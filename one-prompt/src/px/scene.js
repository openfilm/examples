// Ported from mexicat/pdoom-video (MIT, see LICENSE-pdoom-video.txt) and adapted for One Prompt.
// Scene API. A scene owns a time window of the song and renders HDR linear colour
// into the render target it is given. Everything must be a deterministic function of
// time (plus internal state advanced only through render() calls, see `stateful`).
//
// What a scene is given (the engine makes these):
//   ctx (constructor): renderer; audio (beats, onsets, envelopes: px/audio.js); lyrics (px/lyrics.js); comp (a
//     compositor, px/gl.js); W, H (the logical canvas, 1920 × 1080); id and params (its timeline entry, so one scene
//     module can serve several entries); start, end (its window, song seconds).
//   f (each render): t (song seconds); dt (since the frame before; 0 after a seek); lt (seconds since start) and p
//     (0..1 through its window); start, end; seeked (time jumped: stateful scenes reset); preroll (the engine is
//     fast-forwarding a stateful scene); beat, bar (continuous indices from the beat grid) and beatPhase, barPhase
//     (their fractions); a (audio features at t: envelopes 0..1 and decaying hit pulses); under, tin, tout (the
//     scene before's picture during an overlap, and progress through the overlaps in and out).
// render(f, out) draws into `out` (HalfFloat, linear HDR), overwriting all of it, and may return post overrides
// (px/post.js PostParams).

export class Scene {
  /** If true, the engine fast-forwards (calls render with preroll=true) after seeks. */
  stateful = false;
  /** Max seconds of history the engine re-simulates when seeking into a stateful scene. */
  prerollMax = 6;
  /** If true, this scene composites `f.under` itself during its incoming transition. */
  handlesTransition = false;

  constructor(ctx) { this.ctx = ctx; }

  /** Load/create resources. Called once before first render. */
  init() {}

  /** Reset internal state (called on seeks for stateful scenes). */
  reset() {}

  dispose() {}
}
