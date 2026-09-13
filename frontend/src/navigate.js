// Minimal hash-based navigation helper. No router dependency yet — the app
// only has a couple of screens, so a URL hash + hashchange listener (see
// router.jsx) is enough. Swap for react-router-dom if routing needs grow
// (nested routes, params, guards, etc.).
export function navigate(path) {
  window.location.hash = path
}

// Reads the current screen path out of the URL hash. Used by router.jsx to
// pick which screen to show, and by TopNav to know which nav link is active.
export function getCurrentPath() {
  const hash = window.location.hash.replace(/^#/, '')
  return hash || '/'
}
