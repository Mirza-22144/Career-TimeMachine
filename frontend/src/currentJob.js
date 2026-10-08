// Which saved job description the "map for this job" screen should show.
// The app's hash router has no URL parameters, so the id is handed over
// here - set right before navigating, read when that screen loads.
const KEY = "ctm_current_job_description_id";

export function setCurrentJobDescriptionId(id) {
  try {
    sessionStorage.setItem(KEY, id);
  } catch {
    // Storage blocked (private browsing) - the screen falls back to the
    // most recent job description.
  }
}

export function getCurrentJobDescriptionId() {
  try {
    return sessionStorage.getItem(KEY);
  } catch {
    return null;
  }
}
