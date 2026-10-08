// The last roadmap / job map that loaded successfully in this tab, kept
// so AC 3.2.5's exception can be honoured: if results can't be updated
// after a profile change, show the earlier ones with the note "This was
// based on your earlier profile." and a Try Again button.
const key = (name) => `ctm_last_${name}`;

export function rememberResult(name, value) {
  try {
    sessionStorage.setItem(key(name), JSON.stringify(value));
  } catch {
    // No fallback will be available; the normal error state shows instead.
  }
}

export function recallResult(name) {
  try {
    return JSON.parse(sessionStorage.getItem(key(name)));
  } catch {
    return null;
  }
}
