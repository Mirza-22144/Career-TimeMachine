// One-shot flag: set right before navigating from Career Journey's Edit
// button to a wizard step, so that step's Continue button saves and returns
// to Career Journey instead of advancing to the next step in the normal
// linear wizard (AC 3.2.2 / 3.2.3). sessionStorage, not localStorage - this
// only needs to survive the single navigation it was set for.
const EDIT_RETURN_KEY = "ctm_edit_return";

export function setEditReturn() {
  sessionStorage.setItem(EDIT_RETURN_KEY, "1");
}

export function consumeEditReturn() {
  const value = sessionStorage.getItem(EDIT_RETURN_KEY) === "1";
  sessionStorage.removeItem(EDIT_RETURN_KEY);
  return value;
}
