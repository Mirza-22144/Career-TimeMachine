import { useEffect, useMemo, useState } from 'react'
import '../styles/YourStory.css'
import OnboardingSidebar from '../components/OnboardingSidebar'
import sidebarPhoto from '../assets/storyimage.png'
import { stepOneData, buildReflectionText } from '../mockData/onboardingData'
import { SearchIcon, CheckIcon, ArrowRightIcon } from '../components/icons'
import { navigate } from '../navigate.js'
import { api } from '../api.js'

/**
 * Step 1 of the onboarding wizard, shown at the "/your-story" URL, right
 * after the Landing screen's "Enter My Journey" button.
 *
 * Role and years-of-experience options come from the backend catalogue;
 * the selected answers are saved to the real profile via PATCH /profile.
 */
export default function YourStory() {
  const [loading, setLoading] = useState(true)
  const [roles, setRoles] = useState([])
  const [experienceOptions, setExperienceOptions] = useState([])

  const [search, setSearch] = useState('')
  const [selectedRoleId, setSelectedRoleId] = useState(null)
  const [otherRoleText, setOtherRoleText] = useState('')
  const [selectedYearsId, setSelectedYearsId] = useState(null)

  useEffect(() => {
    async function load() {
      const [rolesData, experienceData, profile] = await Promise.all([
        api.getCatalogue('roles'),
        api.getCatalogue('experience-options'),
        api.getProfile(),
      ])
      setRoles(rolesData)
      setExperienceOptions(experienceData)
      if (profile.role_id) setSelectedRoleId(profile.role_id)
      if (profile.role_other_text) setOtherRoleText(profile.role_other_text)
      // Defaults to the first catalogue value (e.g. "1 year") instead of
      // leaving the slider blank, so every value - including the first - is
      // directly selectable without having to drag away and back first.
      setSelectedYearsId(profile.years_experience || experienceData[0]?.id || null)
      setLoading(false)
    }
    load()
  }, [])

  // Capped to 10 - the real catalogue can run into the dozens, and a search
  // narrows it down further if the role isn't in the first 10 shown.
  const filteredRoles = useMemo(() => {
    const query = search.trim().toLowerCase()
    const matches = query ? roles.filter((role) => role.label.toLowerCase().includes(query)) : roles
    return matches.slice(0, 10)
  }, [search, roles])

  const selectedRole = roles.find((r) => r.id === selectedRoleId)
  const isOther = selectedRole?.id === 'other'
  const finalRoleLabel = isOther ? otherRoleText.trim() : selectedRole?.label
  const roleValid = isOther ? !!otherRoleText.trim() : !!selectedRoleId
  const selectedYears = experienceOptions.find((y) => y.id === selectedYearsId)
  const canContinue = roleValid && !!selectedYearsId

  // Slider is index-based over the catalogue's fixed options (1, 2, 3, 5,
  // 7, 10+ years aren't evenly spaced, so dragging steps through the list
  // rather than a raw numeric range).
  const yearsIndex = Math.max(0, experienceOptions.findIndex((y) => y.id === selectedYearsId))
  const yearsPercent = experienceOptions.length > 1 ? (yearsIndex / (experienceOptions.length - 1)) * 100 : 0

  let hint = ''
  if (!selectedRoleId) hint = 'Select a role to continue.'
  else if (isOther && !otherRoleText.trim()) hint = 'Please enter your previous role.'
  else if (!selectedYearsId) hint = 'Select your years of experience to continue.'

  // Saves the role and years chosen on this screen, then moves to step 2.
  // Runs when the Continue button is clicked.
  const handleContinue = async () => {
    await api.patchProfile({
      role_id: selectedRoleId,
      role_other_text: isOther ? otherRoleText.trim() : null,
      years_experience: selectedYearsId,
    })
    navigate('/your-experience')
  }

  if (loading) return <div className="ys-page" />

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
                const isActive = role.id === selectedRoleId
                return (
                  <button
                    type="button"
                    key={role.id}
                    className={`ys-role-card ${isActive ? 'ys-role-card--active' : ''}`}
                    onClick={() => setSelectedRoleId(role.id)}
                    aria-pressed={isActive}
                  >
                    {role.label}
                    <span className={`ys-role-radio ${isActive ? 'ys-role-radio--active' : ''}`}>
                      {isActive && <CheckIcon size={11} />}
                    </span>
                  </button>
                )
              })}
            </div>

            {isOther && (
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
            <div className="ys-slider-card">
              <div className="ys-slider-header">
                <h2 className="ys-question-label">{stepOneData.experienceQuestion}</h2>
                <span className="ys-slider-value">
                  {selectedYears ? <strong>{selectedYears.label}</strong> : <span className="ys-slider-hint">Drag to select</span>}
                </span>
              </div>

              <div className="ys-slider-track-wrap">
                {selectedYears && (
                  <span className="ys-slider-tooltip" style={{ left: `${yearsPercent}%` }}>
                    {selectedYears.label}
                  </span>
                )}
                <input
                  type="range"
                  className="ys-slider-input"
                  style={{ '--percent': `${yearsPercent}%` }}
                  min={0}
                  max={Math.max(0, experienceOptions.length - 1)}
                  step={1}
                  value={yearsIndex}
                  onChange={(e) => setSelectedYearsId(experienceOptions[Number(e.target.value)]?.id)}
                />
              </div>

              <div className="ys-slider-labels">
                <span>{experienceOptions[0]?.label}</span>
                <span>{experienceOptions[experienceOptions.length - 1]?.label}</span>
              </div>
            </div>
          </section>

          {roleValid && selectedYears && (
            <div className="ys-reflection">
              <span className="ys-reflection-icon">
                <CheckIcon size={12} color="#7C3AED" />
              </span>
              <p>{buildReflectionText(finalRoleLabel, selectedYears.label)}</p>
            </div>
          )}

          <button type="button" className="ys-continue" disabled={!canContinue} onClick={handleContinue}>
            {stepOneData.ctaLabel}
            <ArrowRightIcon size={16} />
          </button>
          {!canContinue && <p className="ys-hint">{hint}</p>}
        </div>
      </main>
    </div>
  )
}
