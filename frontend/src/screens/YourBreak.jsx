import { useEffect, useState } from 'react'
import '../styles/YourBreak.css'
import OnboardingSidebar from '../components/OnboardingSidebar'
import SidePhotoPanel from '../components/SidePhotoPanel'
import breakPhoto from '../assets/yourbreak.png'
import { stepThreeData, sidePhoto } from '../mockData/onboardingData'
import { api, ApiError } from '../api.js'
import { navigate } from '../navigate.js'
import { ArrowRightIcon } from '../components/icons'

// Maps confirm-profile's missing-field codes to plain text, since they can
// come from an earlier step (see PROFILE_INCOMPLETE in the API contract).
const MISSING_FIELD_LABELS = {
  role_id: 'your previous role (Step 1)',
  role_other_text: 'your previous role (Step 1)',
  years_experience: 'your years of experience (Step 1)',
  break_started_on: 'when your break started',
  planned_return_date: 'your planned return date',
  valid_break_dates: 'a valid break date range',
}

const CURRENT_YEAR = new Date().getFullYear()
const YEAR_OPTIONS = Array.from({ length: 16 }, (_, i) => CURRENT_YEAR - i)

// The backend stores full ISO dates; the UI only asks for a year (matching
// the approved design), so a break/return is always saved as 1 January of
// the chosen year.
const yearToDate = (year) => (year ? `${year}-01-01` : null)
const dateToYear = (date) => (date ? date.slice(0, 4) : '')

// Step 3 of the onboarding wizard, shown at the "/your-break" URL. Collects
// the career break start/return years and reason, then confirms the whole
// profile before moving on to the Skill Relevance Map.
export default function YourBreak() {
  const [loading, setLoading] = useState(true)
  const [reasons, setReasons] = useState([])

  const [startYear, setStartYear] = useState('')
  const [returnYear, setReturnYear] = useState('')
  const [returnUnsure, setReturnUnsure] = useState(false)
  const [reasonId, setReasonId] = useState(null)
  const [otherReasonText, setOtherReasonText] = useState('')
  const [confirmError, setConfirmError] = useState('')

  useEffect(() => {
    async function load() {
      const [reasonsData, profile] = await Promise.all([api.getCatalogue('break-reasons'), api.getProfile()])
      setReasons(reasonsData)
      setStartYear(dateToYear(profile.break_started_on))
      setReturnYear(dateToYear(profile.planned_return_date))
      setReturnUnsure(profile.return_date_unsure)
      setReasonId(profile.break_reason)
      setOtherReasonText(profile.break_reason_other_text || '')
      setLoading(false)
    }
    load()
  }, [])

  const start = Number(startYear)
  const end = Number(returnYear)
  const bothSelected = !!startYear && (returnUnsure || !!returnYear)
  const isValidRange = bothSelected && (returnUnsure || end >= start)
  const duration = isValidRange && !returnUnsure ? end - start : null
  const timelineYears = duration != null ? Array.from({ length: duration + 1 }, (_, i) => start + i) : []

  const isOtherReason = reasonId === 'other'
  const reasonValid = !isOtherReason || !!otherReasonText.trim()
  const canContinue = isValidRange && reasonValid

  let timelineMessage = ''
  if (!bothSelected) timelineMessage = 'Select both years to see your timeline.'
  else if (!isValidRange) timelineMessage = stepThreeData.invalidRangeMessage

  // Saves the break details, confirms the profile is complete, then moves
  // to the Skill Relevance Map. Runs when the Continue button is clicked.
  const handleContinue = async () => {
    setConfirmError('')
    try {
      await api.patchProfile({
        break_started_on: yearToDate(startYear),
        planned_return_date: returnUnsure ? null : yearToDate(returnYear),
        return_date_unsure: returnUnsure,
        break_reason: reasonId,
        break_reason_other_text: isOtherReason ? otherReasonText.trim() : null,
      })
      await api.confirmProfile()
      navigate('/skill-relevance-map')
    } catch (err) {
      if (err instanceof ApiError && err.code === 'PROFILE_INCOMPLETE' && err.details?.length) {
        const missing = err.details.map((f) => MISSING_FIELD_LABELS[f] || f).join(', ')
        setConfirmError(`Please go back and complete: ${missing}.`)
      } else {
        setConfirmError('Something went wrong saving your answers. Please try again.')
      }
    }
  }

  if (loading) return <div className="yb-page" />

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
              <select
                value={returnYear}
                onChange={(e) => setReturnYear(e.target.value)}
                className="yb-select"
                disabled={returnUnsure}
              >
                <option value="">Select year</option>
                {YEAR_OPTIONS.map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
              <label className="yb-unsure">
                <input
                  type="checkbox"
                  checked={returnUnsure}
                  onChange={(e) => {
                    setReturnUnsure(e.target.checked)
                    if (e.target.checked) setReturnYear('')
                  }}
                />
                I&rsquo;m not sure yet
              </label>
            </div>
          </div>

          <div className="yb-timeline-card">
            <span className="yb-timeline-label">TIMELINE</span>
            {isValidRange && !returnUnsure ? (
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
            ) : isValidRange && returnUnsure ? (
              <p className="yb-timeline-empty">Started {startYear}. Return date to be decided.</p>
            ) : (
              <p className="yb-timeline-empty">{timelineMessage}</p>
            )}
          </div>

          <div className="yb-question-header">
            <h2 className="yb-question-label">{stepThreeData.reasonsLabel}</h2>
            <span className="yb-optional">Optional</span>
          </div>
          <div className="yb-reason-grid">
            {reasons.map((r) => {
              const isActive = reasonId === r.id
              return (
                <button
                  type="button"
                  key={r.id}
                  className={`yb-reason ${isActive ? 'yb-reason--active' : ''}`}
                  onClick={() => setReasonId(isActive ? null : r.id)}
                >
                  {isActive && <span className="yb-reason-check">✓</span>}
                  {r.label}
                </button>
              )
            })}
          </div>
          {isOtherReason && (
            <input
              type="text"
              className="yb-other-input"
              placeholder={stepThreeData.otherReasonPlaceholder}
              value={otherReasonText}
              onChange={(e) => setOtherReasonText(e.target.value)}
              autoFocus
            />
          )}

          <p className="yb-note">{stepThreeData.note}</p>

          <button type="button" className="yb-continue" disabled={!canContinue} onClick={handleContinue}>
            {stepThreeData.ctaLabel}
            <ArrowRightIcon size={16} />
          </button>
          {!canContinue && <p className="yb-hint">{!reasonValid ? 'Please describe your reason.' : timelineMessage}</p>}
          {confirmError && <p className="yb-hint">{confirmError}</p>}
        </div>
      </main>

      <SidePhotoPanel backgroundImage={breakPhoto} label={sidePhoto.label} value={sidePhoto.value} caption={sidePhoto.caption} />
    </div>
  )
}
