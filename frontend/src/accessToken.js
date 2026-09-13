// Client-side mock for the access-token concept ahead of the real backend
// (BE 3.x). Tracks the current session's active token and remembers every
// token generated this session so "enter an existing token" has something
// real to validate against. Swap for real backend calls once they exist -
// callers should only need to change what's inside these functions.

const ACTIVE_TOKEN_KEY = "ctm_active_token";
const KNOWN_TOKENS_KEY = "ctm_known_tokens";

function readKnownTokens() {
  try {
    return JSON.parse(sessionStorage.getItem(KNOWN_TOKENS_KEY) || "[]");
  } catch {
    return [];
  }
}

// Returns the currently active token, or null if none.
export function getActiveToken() {
  return sessionStorage.getItem(ACTIVE_TOKEN_KEY);
}

// True once a token has been generated or successfully entered this session.
export function hasActiveToken() {
  return !!getActiveToken();
}

// Marks a token as active and remembers it as a known/valid token, so it
// can be re-entered later (e.g. after closing the browser tab) and still
// validate successfully.
export function setActiveToken(token) {
  sessionStorage.setItem(ACTIVE_TOKEN_KEY, token);
  const known = readKnownTokens();
  if (!known.includes(token)) {
    known.push(token);
    sessionStorage.setItem(KNOWN_TOKENS_KEY, JSON.stringify(known));
  }
}

// A token is "recognised" if it matches one generated earlier this session.
export function isKnownToken(token) {
  return readKnownTokens().includes(token);
}
