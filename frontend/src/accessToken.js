// The access token IS the real backend session token now (see api.js) - no
// separate mock format and no client-side mapping layer needed.
import { api } from "./api.js";

// Returns the currently active token, or null if none.
export function getActiveToken() {
  return api.getToken();
}

// True once a token has been generated or successfully entered this session.
export function hasActiveToken() {
  return !!api.getToken();
}
