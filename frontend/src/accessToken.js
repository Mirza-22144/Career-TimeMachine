// The access token IS the real backend session token now (see api.js) - no
// separate mock format and no client-side mapping layer needed.
import { api } from "./api.js";

const JUST_RETURNED_KEY = "ctm_just_returned";

// Returns the currently active token, or null if none.
export function getActiveToken() {
  return api.getToken();
}

// True once a token has been generated or successfully entered this session.
export function hasActiveToken() {
  return !!api.getToken();
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
