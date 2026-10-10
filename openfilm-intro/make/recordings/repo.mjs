// The OpenFilm repository the recorders take the desktop app, its chat's marks and Playwright from: OPENFILM_REPO (a
// copy of it, its pages already built: the recordings of one film keep one look while the repository changes under
// them), else a checkout of github.com/openfilm/openfilm next to the examples repository (../openfilm from it).
export const SNAPSHOT = Boolean(process.env.OPENFILM_REPO);
export const REPO = (process.env.OPENFILM_REPO || new URL('../../../../openfilm', import.meta.url).pathname).replace(/\/$/, '');
