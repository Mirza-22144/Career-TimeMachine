// Shared state for the onboarding wizard, persisted across screen
// navigations (each step is its own route/component, so plain component
// state doesn't survive moving between them). Backed by sessionStorage —
// swap for real backend-saved profile data once that exists.
const STORAGE_KEY = 'ctm_onboarding_profile'

function readProfile() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    // sessionStorage can throw (private browsing, disabled storage) —
    // treat as an empty profile rather than crashing the page.
    return {}
  }
}

export function getOnboardingProfile() {
  return readProfile()
}

export function saveOnboardingProfile(patch) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ ...readProfile(), ...patch }))
  } catch {
    // Ignore write failures for the same reason as above.
  }
}
