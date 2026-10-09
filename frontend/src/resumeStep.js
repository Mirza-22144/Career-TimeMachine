import { getCurrentPath, navigate } from './navigate.js'

// Where to send a returning user whose profile isn't confirmed yet, based
// on which of the backend's actual confirmation requirements
// (ProfileService._missing_confirmation_fields) are still missing - not
// just "always start over at Your Story". Your Experience and the Skill
// Relevance Map aren't hard requirements to confirm a profile, so this can
// correctly skip straight to Your Break if Your Story is already done.
export function getResumeStep(profile) {
  const roleDone = !!profile.role_id && (profile.role_id !== 'other' || !!profile.role_other_text)
  if (!roleDone) return '/your-story'

  // At least three skills are needed to confirm (picked and typed-in both count).
  const skillCount = (profile.skill_ids || []).length + (profile.custom_skills || []).length
  if (skillCount < 3) return '/your-experience'

  const breakDone = !!profile.break_started_on && (profile.return_date_unsure || !!profile.planned_return_date)
  if (!breakDone) return '/your-break'

  // Role and break are the only hard requirements the backend checks: if
  // both are already satisfied but confirmation still failed for some
  // other reason (e.g. an "other" break reason with no text entered),
  // Your Break is still the most useful place to land - it's the last
  // step before confirming.
  return '/your-break'
}

const NOTICE_KEY = 'ctm_finish_profile_notice'
export const NOTICE_EVENT = 'ctm:finish-profile'

// Sends her to the first unfinished profile step because she tried to open
// a page that needs a finished profile, and leaves a one-time note so that
// step can explain why she is there (components/FinishProfileNotice.jsx).
export function sendToProfileSetup(profile) {
  try {
    sessionStorage.setItem(NOTICE_KEY, '1')
  } catch {
    // Without storage she is still sent to the right step, just unexplained.
  }
  const step = profile ? getResumeStep(profile) : '/your-story'
  // If she is already on that step the screen does not reload, so the
  // notice there is told directly. Otherwise the step she lands on picks
  // the note up when it opens.
  const alreadyThere = getCurrentPath() === step
  navigate(step)
  if (alreadyThere) window.dispatchEvent(new Event(NOTICE_EVENT))
}

// True while a note from sendToProfileSetup() is waiting. Does not clear it,
// so it is safe to call more than once while a screen is being set up.
export function hasProfileIncompleteNotice() {
  try {
    return sessionStorage.getItem(NOTICE_KEY) === '1'
  } catch {
    return false
  }
}

// True once after sendToProfileSetup(), then false again.
export function consumeProfileIncomplete() {
  try {
    const flagged = sessionStorage.getItem(NOTICE_KEY) === '1'
    sessionStorage.removeItem(NOTICE_KEY)
    return flagged
  } catch {
    return false
  }
}
