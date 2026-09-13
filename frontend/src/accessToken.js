// Client-side mock for the access-token concept ahead of the real backend
// (BE 3.x). Tracks the current session's active token, remembers every
// token generated/entered so "enter an existing token" has something real
// to validate against, and maps each access token to the session token
// behind it so a returning visitor's real saved data comes back. Swap for
// real backend calls once they exist - callers should only need to change
// what's inside these functions.

const ACTIVE_TOKEN_KEY = "ctm_active_token";
// localStorage, not sessionStorage - a token must still be "known" (and its
// session-mapping still resolvable) after the tab that generated it closes,
// otherwise "enter an existing token" could never actually validate.
const KNOWN_TOKENS_KEY = "ctm_known_tokens";
const TOKEN_SESSION_MAP_KEY = "ctm_token_session_map";
const JUST_RETURNED_KEY = "ctm_just_returned";

function readKnownTokens() {
  try {
    return JSON.parse(localStorage.getItem(KNOWN_TOKENS_KEY) || "[]");
  } catch {
    return [];
  }
}

// Returns the currently active token, or null if none. Deliberately
// sessionStorage - a fresh tab should show "Generate/Access Token" again,
// not silently resume, until she explicitly enters her token.
export function getActiveToken() {
  return sessionStorage.getItem(ACTIVE_TOKEN_KEY);
}

// True once a token has been generated or successfully entered this session.
export function hasActiveToken() {
  return !!getActiveToken();
}

// Marks a token as active and remembers it as a known/valid token, so it
// can be re-entered later (even after closing the browser tab) and still
// validate successfully.
export function setActiveToken(token) {
  sessionStorage.setItem(ACTIVE_TOKEN_KEY, token);
  const known = readKnownTokens();
  if (!known.includes(token)) {
    known.push(token);
    localStorage.setItem(KNOWN_TOKENS_KEY, JSON.stringify(known));
  }
}

// A token is "recognised" if it matches one generated/entered earlier.
export function isKnownToken(token) {
  return readKnownTokens().includes(token);
}

// Remembers which session token a given access token belongs to, so
// re-entering the access token later can restore the same session (and
// therefore the same saved profile/career-journey data). No internal
// try/catch here on purpose - a storage failure here is exactly what
// AC 3.2.1's "couldn't be saved" exception is meant to catch, so it should
// propagate to the caller rather than fail silently.
export function recordTokenSession(accessToken, sessionToken) {
  const map = JSON.parse(localStorage.getItem(TOKEN_SESSION_MAP_KEY) || "{}");
  map[accessToken] = sessionToken;
  localStorage.setItem(TOKEN_SESSION_MAP_KEY, JSON.stringify(map));
}

// Looks up the session token behind an access token, or undefined if there
// is no mapping (e.g. the token was generated on a different browser, or
// local storage was cleared).
export function getSessionForToken(accessToken) {
  const map = JSON.parse(localStorage.getItem(TOKEN_SESSION_MAP_KEY) || "{}");
  return map[accessToken];
}

// One-shot flag: set right before navigating to Career Journey after a
// successful existing-token entry, so that page can show "Welcome back"
// instead of its normal heading - but only that one time, not on every
// later visit via the nav.
export function setJustReturned() {
  sessionStorage.setItem(JUST_RETURNED_KEY, "1");
}

export function consumeJustReturned() {
  const value = sessionStorage.getItem(JUST_RETURNED_KEY) === "1";
  sessionStorage.removeItem(JUST_RETURNED_KEY);
  return value;
}
