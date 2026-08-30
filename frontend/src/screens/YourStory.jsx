import { useMemo, useState } from 'react'
import '../styles/YourStory.css'
import OnboardingSidebar from '../components/OnboardingSidebar'
import sidebarPhoto from '../assets/storyimage.png'
import { stepOneData, buildReflectionText } from '../mockData/onboardingData'
import { SearchIcon, CheckIcon, ArrowRightIcon } from '../components/icons'
import { navigate } from '../navigate.js'
import { getOnboardingProfile, saveOnboardingProfile } from '../onboardingState.js'

/**
 * "Your Story" — step 1 of the 5-step onboarding wizard shown after the
 * Landing screen's "Enter My Journey" CTA.
 *
 * Unlike the Landing screen's demo sections, this is a real data-collection
 * form (previous role + years of experience), so its controls stay fully
 * interactive rather than fixed.
 */
export default function YourStory() {
  const [profile] = useState(getOnboardingProfile)
  const isKnownRole = profile.role && stepOneData.roles.includes(profile.role)

  const [search, setSearch] = useState('')
  // Single-select — clicking a role replaces the previous selection.
  // Restores a prior answer if the user navigated back to fix something.
  const [selectedRole, setSelectedRole] = useState(isKnownRole ? profile.role : profile.role ? 'Other' : null)
  const [otherRoleText, setOtherRoleText] = useState(isKnownRole ? '' : (profile.role ?? ''))
  // Tracks whether the slider has actually been touched, so a valid-looking
  // default value doesn't count as an answer.
  const [yearsTouched, setYearsTouched] = useState(profile.years != null)
  const [years, setYears] = useState(profile.years ?? stepOneData.minYears)

  const filteredRoles = useMemo(() => {
    const query = search.trim().toLowerCase()
    if (!query) return stepOneData.roles
    return stepOneData.roles.filter((role) => role.toLowerCase().includes(query))
  }, [search])

  const percent = ((years - stepOneData.minYears) / (stepOneData.maxYears - stepOneData.minYears)) * 100
  const yearsLabel = years >= stepOneData.maxYears ? `${years}+` : `${years}`

  const finalRole = selectedRole === 'Other' ? otherRoleText.trim() : selectedRole
  const roleValid = !!finalRole
  const canContinue = roleValid && yearsTouched

  let hint = ''
  if (!selectedRole) hint = 'Select a role to continue.'
  else if (selectedRole === 'Other' && !otherRoleText.trim()) hint = 'Please enter your previous role.'
  else if (!yearsTouched) hint = 'Drag the slider to select your years of experience.'

  return (
    <div className="ys-page">
      <OnboardingSidebar currentStep={1} backgroundImage={sidebarPhoto} />

      <main className="ys-form-panel">
        <div className="ys-form-content">
          <span className="ys-eyebrow">{stepOneData.eyebrow}</span>
          <h1 className="ys-heading">{stepOneData.heading}</h1>
          <p className="ys-subheading">{stepOneData.subheading}</p>

          <section className="ys-question">
            <h2 className="ys-question-label">{stepOneData.roleQuestion}</h2>

            <div className="ys-search">
              <SearchIcon size={16} color="#9CA3AF" />
              <input
                type="text"
                className="ys-search-input"
                placeholder={stepOneData.searchPlaceholder}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <div className="ys-role-grid">
              {filteredRoles.map((role) => {
                const isActive = role === selectedRole
                return (
                  <button
                    type="button"
                    key={role}
                    className={`ys-role-card ${isActive ? 'ys-role-card--active' : ''}`}
                    onClick={() => setSelectedRole(role)}
                    aria-pressed={isActive}
                  >
                    {role}
                    <span className={`ys-role-radio ${isActive ? 'ys-role-radio--active' : ''}`}>
                      {isActive && <CheckIcon size={11} />}
                    </span>
                  </button>
                )
              })}
            </div>

            {selectedRole === 'Other' && (
              <input
                type="text"
                className="ys-other-input"
                placeholder="What was your previous role?"
                value={otherRoleText}
                onChange={(e) => setOtherRoleText(e.target.value)}
                autoFocus
              />
            )}
          </section>

          <section className="ys-question">
            <h2 className="ys-question-label">{stepOneData.experienceQuestion}</h2>

            <div className="ys-slider-card">
              <div className="ys-slider-header">
                <span className="ys-slider-value">
                  <strong>{years}</strong> years
                </span>
                <span className="ys-slider-hint">Drag to select</span>
              </div>

              <div className="ys-slider-track-wrap">
                <input
                  type="range"
                  min={stepOneData.minYears}
                  max={stepOneData.maxYears}
                  value={years}
                  onChange={(e) => {
                    setYears(Number(e.target.value))
                    setYearsTouched(true)
                  }}
                  className="ys-slider-input"
                  style={{ '--percent': `${percent}%` }}
                  aria-label={stepOneData.experienceQuestion}
                />
                <span className="ys-slider-tooltip" style={{ left: `${percent}%` }}>
                  {yearsLabel} yrs
                </span>
              </div>

              <div className="ys-slider-labels">
                <span>{stepOneData.minYears} yr</span>
                <span>{stepOneData.maxYears}+ yrs</span>
              </div>
            </div>
          </section>

          {roleValid && yearsTouched && (
            <div className="ys-reflection">
              <span className="ys-reflection-icon">
                <CheckIcon size={12} color="#7C3AED" />
              </span>
              <p>{buildReflectionText(finalRole, years)}</p>
            </div>
          )}

          <button
            type="button"
            className="ys-continue"
            disabled={!canContinue}
            onClick={() => {
              saveOnboardingProfile({ role: finalRole, years })
              navigate('/your-experience')
            }}
          >
            {stepOneData.ctaLabel}
            <ArrowRightIcon size={16} />
          </button>
          {!canContinue && <p className="ys-hint">{hint}</p>}
        </div>
      </main>
    </div>
  )
}
