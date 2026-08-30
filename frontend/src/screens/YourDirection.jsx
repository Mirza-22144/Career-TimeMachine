import { useState } from 'react'
import '../styles/YourDirection.css'
import OnboardingSidebar from '../components/OnboardingSidebar'
import { stepFourData, stepFiveData } from '../mockData/onboardingData'
import { getOnboardingProfile, saveOnboardingProfile } from '../onboardingState.js'
import { CheckIcon, ArrowRightIcon } from '../components/icons'

export default function YourDirection() {
  const [profile] = useState(getOnboardingProfile)
  // Restores prior answers if the user navigated back to fix something.
  const [pace, setPace] = useState(profile.pace ?? null)
  const [exploreAreas, setExploreAreas] = useState(profile.exploreAreas ?? [])
  const [tryFirst, setTryFirst] = useState(profile.tryFirst ?? null)

  const skills = profile.skills || []
  const responsibilities = profile.responsibilities || []

  const plural = (n, word) => {
    if (n === 1) return `${n} ${word}`
    return `${n} ${word.endsWith('y') ? word.slice(0, -1) + 'ies' : word + 's'}`
  }

  const journey = [
    { label: 'Your Story', caption: profile.role ? `${profile.role}, ${plural(profile.years, 'yr')}` : '—' },
    { label: 'Your Experience', caption: `${plural(skills.length, 'skill')}, ${plural(responsibilities.length, 'duty')}` },
    { label: 'Your Break', caption: profile.breakStartYear ? `${profile.breakStartYear} to ${profile.breakReturnYear}` : '—' },
    { label: 'Journey Map', caption: `${skills.length} kept, ${stepFourData.newHorizons.length} new` },
  ]

  const toggleExplore = (area) => {
    setExploreAreas((prev) => {
      const next = prev.includes(area) ? prev.filter((a) => a !== area) : [...prev, area]
      if (!next.includes(tryFirst)) setTryFirst(null)
      return next
    })
  }

  const canContinue = pace && exploreAreas.length > 0 && tryFirst

  return (
    <div className="yd-page">
      <OnboardingSidebar currentStep={5} showPhoto={false} />

      <main className="yd-form-panel">
        <div className="yd-form-content">
          <span className="yd-eyebrow">{stepFiveData.eyebrow}</span>
          <h1 className="yd-heading">{stepFiveData.heading}</h1>
          <p className="yd-subheading">{stepFiveData.subheading}</p>

          <div className="yd-journey-card">
            <div className="yd-journey-header">
              <span>{stepFiveData.journeyLabel}</span>
              <span>{journey.length} steps mapped</span>
            </div>
            <div className="yd-journey-row">
              {journey.map((step) => (
                <div key={step.label} className="yd-journey-step">
                  <span className="yd-journey-dot yd-journey-dot--done">
                    <CheckIcon size={12} color="#FFFFFF" />
                  </span>
                  <span className="yd-journey-label">{step.label}</span>
                  <span className="yd-journey-caption">{step.caption}</span>
                </div>
              ))}
              <div className="yd-journey-step">
                <span className="yd-journey-dot yd-journey-dot--current" />
                <span className="yd-journey-label">You are here</span>
                <span className="yd-journey-caption">Your Direction</span>
              </div>
            </div>
          </div>

          <h2 className="yd-question-label">{stepFiveData.paceQuestion}</h2>
          <p className="yd-question-subtext">{stepFiveData.paceSubtext}</p>
          <div className="yd-pace-grid">
            {stepFiveData.paceOptions.map((option) => {
              const isActive = pace === option.title
              return (
                <button
                  type="button"
                  key={option.title}
                  className={`yd-pace-card ${isActive ? 'yd-pace-card--active' : ''}`}
                  onClick={() => setPace(option.title)}
                >
                  <span className={`yd-pace-bar ${isActive ? 'yd-pace-bar--active' : ''}`} />
                  <strong>{option.title}</strong>
                  <span>{option.caption}</span>
                </button>
              )
            })}
          </div>

          <h2 className="yd-question-label">{stepFiveData.exploreQuestion}</h2>
          <p className="yd-question-subtext">{stepFiveData.exploreSubtext}</p>
          <div className="yd-pill-grid">
            {stepFiveData.exploreAreas.map((area) => {
              const isActive = exploreAreas.includes(area)
              return (
                <button
                  type="button"
                  key={area}
                  className={`yd-pill ${isActive ? 'yd-pill--active' : ''}`}
                  onClick={() => toggleExplore(area)}
                >
                  {isActive && <CheckIcon size={11} color="#FFFFFF" />}
                  {area}
                </button>
              )
            })}
          </div>

          <div className="yd-question-header">
            <h2 className="yd-question-label">{stepFiveData.tryQuestion}</h2>
            <span className="yd-optional">Pick one</span>
          </div>
          <p className="yd-question-subtext">{stepFiveData.trySubtext}</p>
          <div className="yd-radio-grid">
            {exploreAreas.length === 0 && <p className="yd-radio-empty">Select at least one area above.</p>}
            {exploreAreas.map((area) => {
              const isActive = tryFirst === area
              return (
                <button
                  type="button"
                  key={area}
                  className={`yd-radio ${isActive ? 'yd-radio--active' : ''}`}
                  onClick={() => setTryFirst(area)}
                >
                  <span className={`yd-radio-dot ${isActive ? 'yd-radio-dot--active' : ''}`} />
                  {area}
                </button>
              )
            })}
          </div>

          <div className="yd-note">
            <strong>{stepFiveData.noteTitle}</strong>
            <p>{stepFiveData.noteBody}</p>
          </div>

          <button
            type="button"
            className="yd-continue"
            disabled={!canContinue}
            onClick={() => saveOnboardingProfile({ pace, exploreAreas, tryFirst })}
          >
            {stepFiveData.ctaLabel}
            <ArrowRightIcon size={16} />
          </button>
        </div>
      </main>
    </div>
  )
}
