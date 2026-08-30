import { useState } from 'react'
import '../styles/YourBreak.css'
import OnboardingSidebar from '../components/OnboardingSidebar'
import SidePhotoPanel from '../components/SidePhotoPanel'
import breakPhoto from '../assets/yourbreak.png'
import { stepThreeData, sidePhoto } from '../mockData/onboardingData'
import { getOnboardingProfile, saveOnboardingProfile } from '../onboardingState.js'
import { navigate } from '../navigate.js'
import { ArrowRightIcon } from '../components/icons'

const CURRENT_YEAR = new Date().getFullYear()
const YEAR_OPTIONS = Array.from({ length: 16 }, (_, i) => CURRENT_YEAR - i)

export default function YourBreak() {
  const [profile] = useState(getOnboardingProfile)
  // Restores prior answers if the user navigated back to fix something.
  const [startYear, setStartYear] = useState(profile.breakStartYear ?? '')
  const [returnYear, setReturnYear] = useState(profile.breakReturnYear ?? '')
  const [reasons, setReasons] = useState(profile.breakReasons ?? [])

  const toggleReason = (reason) => {
    setReasons((prev) => (prev.includes(reason) ? prev.filter((r) => r !== reason) : [...prev, reason]))
  }

  const start = Number(startYear)
  const end = Number(returnYear)
  const hasRange = startYear && returnYear && end >= start
  const duration = hasRange ? end - start : null
  const timelineYears = hasRange ? Array.from({ length: duration + 1 }, (_, i) => start + i) : []

  const canContinue = hasRange

  return (
    <div className="yb-page">
      <OnboardingSidebar currentStep={3} showPhoto={false} />

      <main className="yb-form-panel">
        <div className="yb-form-content">
          <span className="yb-eyebrow">{stepThreeData.eyebrow}</span>
          <h1 className="yb-heading">{stepThreeData.heading}</h1>
          <p className="yb-subheading">{stepThreeData.subheading}</p>

          <div className="yb-year-row">
            <div className="yb-year-field">
              <label className="yb-year-label">{stepThreeData.startLabel}</label>
              <select value={startYear} onChange={(e) => setStartYear(e.target.value)} className="yb-select">
                <option value="">Select year</option>
                {YEAR_OPTIONS.map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>
            <div className="yb-year-field">
              <label className="yb-year-label">{stepThreeData.returnLabel}</label>
              <select value={returnYear} onChange={(e) => setReturnYear(e.target.value)} className="yb-select">
                <option value="">Select year</option>
                {YEAR_OPTIONS.map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="yb-timeline-card">
            <span className="yb-timeline-label">TIMELINE</span>
            {hasRange ? (
              <>
                <div className="yb-timeline-ticks">
                  {timelineYears.map((y) => (
                    <span key={y}>{y}</span>
                  ))}
                </div>
                <div className="yb-timeline-track">
                  <div className="yb-timeline-fill" />
                </div>
                <div className="yb-timeline-duration">
                  <span>Career break duration</span>
                  <strong>{duration} {duration === 1 ? 'year' : 'years'}</strong>
                </div>
              </>
            ) : (
              <p className="yb-timeline-empty">Select both years to see your timeline.</p>
            )}
          </div>

          <div className="yb-question-header">
            <h2 className="yb-question-label">{stepThreeData.reasonsLabel}</h2>
            <span className="yb-optional">Optional</span>
          </div>
          <div className="yb-reason-grid">
            {stepThreeData.reasons.map((reason) => {
              const isActive = reasons.includes(reason)
              return (
                <button
                  type="button"
                  key={reason}
                  className={`yb-reason ${isActive ? 'yb-reason--active' : ''}`}
                  onClick={() => toggleReason(reason)}
                >
                  {isActive && <span className="yb-reason-check">✓</span>}
                  {reason}
                </button>
              )
            })}
          </div>

          <p className="yb-note">{stepThreeData.note}</p>

          <button
            type="button"
            className="yb-continue"
            disabled={!canContinue}
            onClick={() => {
              saveOnboardingProfile({ breakStartYear: start, breakReturnYear: end, breakReasons: reasons })
              navigate('/skill-relevance-map')
            }}
          >
            {stepThreeData.ctaLabel}
            <ArrowRightIcon size={16} />
          </button>
        </div>
      </main>

      <SidePhotoPanel backgroundImage={breakPhoto} label={sidePhoto.label} value={sidePhoto.value} caption={sidePhoto.caption} />
    </div>
  )
}
