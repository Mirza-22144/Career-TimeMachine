// Thin client for the CareerTimeMachine backend (see backend/docs/API-CONTRACT.md).
// Handles the anonymous-session token and the standard error envelope
// ({ error: { code, message, details } }) in one place.

const API_BASE = 'http://localhost:8000/api/v1'
const TOKEN_KEY = 'ctm_session_token'

function getToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

function setToken(token) {
  try {
    sessionStorage.setItem(TOKEN_KEY, token)
  } catch {
    // ignore — same private-browsing fallback as onboardingState.js
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
    // A dead/expired session — start a fresh one and retry once.
    if (res.status === 401 && auth) {
      await createSession(true)
      return request(path, { method, body, auth })
    }
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

export const api = {
  createSession,
  getCatalogue: (kind) => request(`/catalogue/${kind}`),
  getProfile: () => request('/profile'),
  patchProfile: (patch) => request('/profile', { method: 'PATCH', body: patch }),
  confirmProfile: () => request('/profile/confirm', { method: 'POST' }),
  getCareerJourney: () => request('/career-journey'),
  getCareerTranslation: () => request('/career-translation'),
  getCareerDirection: () => request('/career-direction'),
  patchCareerDirection: (patch) => request('/career-direction', { method: 'PATCH', body: patch }),
}

export { ApiError }
