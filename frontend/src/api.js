// Thin client for the CareerTimeMachine backend (see backend/docs/API-CONTRACT.md).
// Handles the anonymous-session token and the standard error envelope
// ({ error: { code, message, details } }) in one place.

// Set VITE_API_BASE_URL at build time to point at a deployed backend (see
// DEPLOYMENT.md). Falls back to local dev otherwise - 127.0.0.1, not
// "localhost", since resolving "localhost" adds a ~2s IPv6-then-fallback
// delay on some Windows setups; 127.0.0.1 skips that entirely.
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const TOKEN_KEY = 'ctm_session_token'

// Reads the saved session token, if any. Used by request() below to attach
// the token to every call, and to check if a session already exists.
function getToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

// Saves the session token so later page loads reuse the same session.
// Used right after a new session is created.
function setToken(token) {
  try {
    sessionStorage.setItem(TOKEN_KEY, token)
  } catch {
    // Storage can be blocked in private browsing. Skip saving the token in
    // that case instead of crashing the page.
  }
}

class ApiError extends Error {
  constructor(code, message, details) {
    super(message)
    this.code = code
    this.details = details
  }
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth) {
    const token = getToken() || (await createSession())
    headers['X-Session-Token'] = token
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  if (res.status === 204) return null

  const json = await res.json().catch(() => null)

  if (!res.ok) {
    const err = json?.error || { code: `HTTP_${res.status}`, message: 'Request failed', details: [] }
    throw new ApiError(err.code, err.message, err.details)
  }

  return json
}

// Creates a new anonymous session and stores its token. `force` skips the
// "already have a token" check (used when the current one is invalid).
async function createSession(force = false) {
  if (!force) {
    const existing = getToken()
    if (existing) return existing
  }
  const session = await request('/anonymous-sessions', { method: 'POST', auth: false })
  setToken(session.token)
  return session.token
}

// Checks whether a given token is recognised by the backend, without
// switching the active session to it - used to validate a token the user
// just typed in before committing to it via restoreSession(). Returns
// true/false for a definitive answer; throws for anything else (network
// failure, 5xx) so the caller can tell "not recognised" apart from
// "couldn't check".
async function validateToken(token) {
  const res = await fetch(`${API_BASE}/anonymous-sessions/current`, {
    headers: { 'X-Session-Token': token },
  })
  if (res.status === 401) return false
  if (!res.ok) {
    const json = await res.json().catch(() => null)
    const err = json?.error || { code: `HTTP_${res.status}`, message: 'Request failed', details: [] }
    throw new ApiError(err.code, err.message, err.details)
  }
  return true
}

export const api = {
  createSession,
  validateToken,
  getToken,
  // Points future requests at a specific, already-validated token - used to
  // restore a returning visitor's session once her entered access token has
  // been confirmed via validateToken().
  restoreSession: (token) => setToken(token),
  getCatalogue: (kind) => request(`/catalogue/${kind}`),
  // Skills depend on the previously selected role — omit roleId for the flat fallback list.
  getSkills: (roleId) => request(`/catalogue/skills${roleId ? `?role_id=${encodeURIComponent(roleId)}` : ''}`),
  getProfile: () => request('/profile'),
  patchProfile: (patch) => request('/profile', { method: 'PATCH', body: patch }),
  confirmProfile: () => request('/profile/confirm', { method: 'POST' }),
  getCareerJourney: () => request('/career-journey'),
  getCareerTranslation: () => request('/career-translation'),
  getCareerDirection: () => request('/career-direction'),
  patchCareerDirection: (patch) => request('/career-direction', { method: 'PATCH', body: patch }),
}

export { ApiError }
