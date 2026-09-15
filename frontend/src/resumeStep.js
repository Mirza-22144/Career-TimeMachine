// Where to send a returning user whose profile isn't confirmed yet, based
// on which of the backend's actual confirmation requirements
// (ProfileService._missing_confirmation_fields) are still missing - not
// just "always start over at Your Story". Your Experience and the Skill
// Relevance Map aren't hard requirements to confirm a profile, so this can
// correctly skip straight to Your Break if Your Story is already done.
export function getResumeStep(profile) {
  const roleDone = !!profile.role_id && (profile.role_id !== 'other' || !!profile.role_other_text)
  if (!roleDone) return '/your-story'

  const breakDone = !!profile.break_started_on && (profile.return_date_unsure || !!profile.planned_return_date)
  if (!breakDone) return '/your-break'

  // Role and break are the only hard requirements the backend checks: if
  // both are already satisfied but confirmation still failed for some
  // other reason (e.g. an "other" break reason with no text entered),
  // Your Break is still the most useful place to land - it's the last
  // step before confirming.
  return '/your-break'
}
