// Ported from mexicat/pdoom-video (MIT, see LICENSE-pdoom-video.txt) and adapted for One Prompt.
/**
 * Physical pixels per logical pixel of the output. A 4K render shoots the 1920×1080 page at device scale 2,
 * so every render target follows it (true 3840×2160, not an upscale).
 */
export const SCALE = typeof window !== 'undefined' && window.devicePixelRatio >= 1.5 ? 2 : 1;
