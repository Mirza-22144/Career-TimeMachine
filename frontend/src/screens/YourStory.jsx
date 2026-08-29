import { useMemo, useState } from 'react'
import '../styles/YourStory.css'
import OnboardingSidebar from '../components/OnboardingSidebar'
import sidebarPhoto from '../assets/storyimage.png'
import { stepOneData, buildReflectionText } from '../mockData/onboardingData'
import { SearchIcon, CheckIcon, ArrowRightIcon } from '../components/icons'

/**
 * "Your Story" — step 1 of the 5-step onboarding wizard shown after the
 * Landing screen's "Enter My Journey" CTA.
 *
 * Unlike the Landing screen's demo sections, this is a real data-collection
 * form (previous role + years of experience), so its controls stay fully
 * interactive rather than fixed.
 *
 * Steps 2-5 aren't built yet — advancing past this step has nowhere to go
 * until their designs arrive.
 */
export default function YourStory() {
  const [search, setSearch] = useState('')
  const [selectedRoles, setSelectedRoles] = useState([])
  // Rests at the minimum rather than a guessed midpoint, so nothing reads
  // as pre-selected before the user actually drags the slider.
  const [years, setYears] = useState(stepOneData.minYears)

  const filteredRoles = useMemo(() => {
    const query = search.trim().toLowerCase()
    if (!query) return stepOneData.roles
    return stepOneData.roles.filter((role) => role.toLowerCase().includes(query))
  }, [search])

  const toggleRole = (role) => {
    setSelectedRoles((prev) =>
      prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role],
    )
  }

  const percent = ((years - stepOneData.minYears) / (stepOneData.maxYears - stepOneData.minYears)) * 100
  const yearsLabel = years >= stepOneData.maxYears ? `${years}+` : `${years}`

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
                const isActive = selectedRoles.includes(role)
                return (
                  <button
                    type="button"
                    key={role}
                    className={`ys-role-card ${isActive ? 'ys-role-card--active' : ''}`}
                    onClick={() => toggleRole(role)}
                    aria-pressed={isActive}
                  >
                    {role}
                    <span className={`ys-role-checkbox ${isActive ? 'ys-role-checkbox--active' : ''}`}>
                      {isActive && <CheckIcon size={11} />}
                    </span>
                  </button>
                )
              })}
            </div>
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
                  onChange={(e) => setYears(Number(e.target.value))}
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

          {selectedRoles.length > 0 && (
            <div className="ys-reflection">
              <span className="ys-reflection-icon">
                <CheckIcon size={12} color="#7C3AED" />
              </span>
              <p>{buildReflectionText(selectedRoles, years)}</p>
            </div>
          )}

          <button type="button" className="ys-continue" disabled={selectedRoles.length === 0}>
            {stepOneData.ctaLabel}
            <ArrowRightIcon size={16} />
          </button>
        </div>
      </main>
    </div>
  )
}
