// Minimal hash-based navigation helper. No router dependency yet — the app
// only has a couple of screens, so a URL hash + hashchange listener (see
// router.jsx) is enough. Swap for react-router-dom if routing needs grow
// (nested routes, params, guards, etc.).
export function navigate(path) {
  window.location.hash = path
}
