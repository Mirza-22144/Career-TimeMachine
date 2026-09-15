// Carries the role Maya selects on Your Direction into the Workplace
// Scenario practice flow (AC 4.1.2). sessionStorage, not the backend - the
// backend's career-direction endpoint still expects the old fixed
// career-area catalogue, which this role-choice screen replaces on the
// frontend ahead of a real backend contract. Swap for a real backend call
// once BE/AI catch up - callers should only need to change what's inside
// these functions.
const SELECTED_ROLE_KEY = "ctm_selected_role";
const PRACTICE_STATE_KEY = "ctm_practice_state";

export function setSelectedRole(role) {
  sessionStorage.setItem(SELECTED_ROLE_KEY, JSON.stringify(role));
}

export function getSelectedRole() {
  try {
    return JSON.parse(sessionStorage.getItem(SELECTED_ROLE_KEY));
  } catch {
    return null;
  }
}

// AC 4.3.4: the active practice session (role, duration, difficulty), set
// once Maya enters the workplace. Read back on later visits (nav away and
// back, or a reload) so she resumes the same session instead of starting
// the intro over.
export function setPracticeState(state) {
  sessionStorage.setItem(PRACTICE_STATE_KEY, JSON.stringify(state));
}

export function getPracticeState() {
  try {
    return JSON.parse(sessionStorage.getItem(PRACTICE_STATE_KEY));
  } catch {
    return null;
  }
}
