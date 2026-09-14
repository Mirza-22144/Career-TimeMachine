// Carries the role Maya selects on Your Direction into the Workplace
// Scenario practice flow (AC 4.1.2). sessionStorage, not the backend - the
// backend's career-direction endpoint still expects the old fixed
// career-area catalogue, which this role-choice screen replaces on the
// frontend ahead of a real backend contract. Swap for a real backend call
// once BE/AI catch up - callers should only need to change what's inside
// these functions.
const SELECTED_ROLE_KEY = "ctm_selected_role";

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
