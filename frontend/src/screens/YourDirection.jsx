import { useEffect, useState } from 'react'
import '../styles/YourDirection.css'
import OnboardingSidebar from '../components/OnboardingSidebar'
import TopNav from '../components/TopNav'
import { stepFiveData, paceCaptions } from '../mockData/onboardingData'
import { getPredictedRoles } from '../mockData/predictedRoles'
import { setSelectedRole as savePracticeRole } from '../practiceSession.js'
import { api } from '../api.js'
import { navigate } from '../navigate.js'
import { CheckIcon, ArrowRightIcon } from '../components/icons'

// Adds an "s" (or turns "y" into "ies") when the count is more than one.
// Used to build the small journey-recap captions on this screen.
const plural = (n, word) => {
  if (n === 1) return `${n} ${word}`
  return `${n} ${word.endsWith('y') ? word.slice(0, -1) + 'ies' : word + 's'}`
}

// Step 5 of the onboarding wizard, shown at the "/your-direction" URL.
// Recaps the journey so far, then collects return-readiness and the area
// the user wants to explore.
export default function YourDirection() {
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)
  const [journey, setJourney] = useState(null)
  const [translation, setTranslation] = useState(null)
  const [returnStatuses, setReturnStatuses] = useState([])
  const [pace, setPace] = useState(null)
  // { type: 'previous' | 'predicted', id, label } - nothing is selected by
  // default; Maya must explicitly pick a role (AC 4.1.2's "no role
  // selected" exception is a real, reachable state, not just a fallback).
  const [selectedRole, setSelectedRole] = useState(null)

  const load = async () => {
    try {
      const [journeyData, statuses, direction, translationData] = await Promise.all([
        api.getCareerJourney(),
        api.getCatalogue('return-statuses'),
        api.getCareerDirection(),
        api.getCareerTranslation(),
      ])
      setJourney(journeyData)
      setTranslation(translationData)
      setReturnStatuses(statuses)
      setPace(direction.return_readiness)
      setLoading(false)
    } catch {
      setLoadError(true)
      setLoading(false)
    }
  }

  useEffect(() => {
    async function run() {
      await load()
    }
    run()
  }, [])

  const retryLoad = () => {
    setLoading(true)
    setLoadError(false)
    load()
  }

  const canContinue = !!pace && !!selectedRole

  let hint = ''
  if (!pace) hint = 'Select a return status to continue.'
  else if (!selectedRole) hint = 'Please select a role to continue.' // AC 4.1.2's exact exception copy

  // Saves the chosen pace, carries the selected role into the practice
  // session (AC 4.1.2), then moves into the Workplace Scenario intro -
  // Career Journey is reached later via the nav, not as part of finishing
  // the wizard. Runs when Continue is clicked.
  const handleContinue = async () => {
    savePracticeRole(selectedRole)
    await api.patchCareerDirection({ return_readiness: pace })
    navigate('/workplace-scenario')
  }

  if (loading) return (
    <>
      <TopNav />
      <div className="yd-page" />
    </>
  )

  if (loadError) return (
    <>
      <TopNav />
      <div className="yd-page">
        <div className="yd-load-error">
          <p>We couldn&rsquo;t load the information needed for this activity. Please try again.</p>
          <button type="button" onClick={retryLoad}>Try Again</button>
        </div>
      </div>
    </>
  )

  const skillCount = journey.selected_skills.catalogue_skills.length + journey.selected_skills.custom_skills.length
  const ownedCount = translation.owned_skills.length + translation.custom_skills.length
  const newHorizonsCount = translation.new_horizons.length
  const journeySteps = [
    { label: 'Your Story', caption: journey.previous_role ? `${journey.previous_role.label}, ${journey.years_experience.label}` : '—' },
    { label: 'Your Experience', caption: `${plural(skillCount, 'skill')}` },
    {
      label: 'Your Break',
      caption: journey.career_break.break_started_on
        ? `${journey.career_break.break_started_on.slice(0, 4)} to ${journey.career_break.return_date_unsure ? 'undecided' : journey.career_break.planned_return_date?.slice(0, 4)}`
        : '—',
    },
    { label: 'Journey Map', caption: `${ownedCount} kept, ${newHorizonsCount} new` },
  ]

  const predictedRoles = journey.previous_role ? getPredictedRoles(journey.previous_role.id) : []

  return (
    <>
      <TopNav />
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
              <span>{journeySteps.length} steps mapped</span>
            </div>
            <div className="yd-journey-row">
              {journeySteps.map((step) => (
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
            {returnStatuses.map((option) => {
              const isActive = pace === option.id
              return (
                <button
                  type="button"
                  key={option.id}
                  className={`yd-pace-card ${isActive ? 'yd-pace-card--active' : ''}`}
                  onClick={() => setPace(option.id)}
                >
                  <span className={`yd-pace-bar ${isActive ? 'yd-pace-bar--active' : ''}`} />
                  <strong>{option.label}</strong>
                  <span>{paceCaptions[option.id]}</span>
                </button>
              )
            })}
          </div>

          <h2 className="yd-question-label">{stepFiveData.rolesQuestion}</h2>
          <p className="yd-question-subtext">{stepFiveData.rolesSubtext}</p>
          <div className="yd-role-grid">
            {journey.previous_role && (
              <button
                type="button"
                className={`yd-role-card ${selectedRole?.type === 'previous' ? 'yd-role-card--active' : ''}`}
                onClick={() => setSelectedRole({ type: 'previous', id: journey.previous_role.id, label: journey.previous_role.label })}
              >
                <span className="yd-role-badge">YOUR PREVIOUS ROLE</span>
                <div className="yd-role-header">
                  <strong>{journey.previous_role.label}</strong>
                  <span className={`yd-role-check ${selectedRole?.type === 'previous' ? 'yd-role-check--active' : ''}`}>
                    {selectedRole?.type === 'previous' && <CheckIcon size={11} color="#FFFFFF" />}
                  </span>
                </div>
                <p>Your previous role. Practise with the experience you already have.</p>
              </button>
            )}

            {predictedRoles.map((role) => {
              const isActive = selectedRole?.type === 'predicted' && selectedRole.id === role.id
              return (
                <button
                  type="button"
                  key={role.id}
                  className={`yd-role-card ${isActive ? 'yd-role-card--active' : ''}`}
                  onClick={() => setSelectedRole({ type: 'predicted', id: role.id, label: role.label })}
                >
                  <span className="yd-role-badge yd-role-badge--predicted">PREDICTED ROLE</span>
                  <div className="yd-role-header">
                    <strong>{role.label}</strong>
                    <span className={`yd-role-radio ${isActive ? 'yd-role-radio--active' : ''}`} />
                  </div>
                  <p>{role.description}</p>
                </button>
              )
            })}
          </div>
          {predictedRoles.length === 0 && (
            <p className="yd-role-note">
              We couldn&rsquo;t generate career suggestions right now. You can continue with your previous role.
            </p>
          )}

          <div className="yd-note">
            <strong>{stepFiveData.noteTitle}</strong>
            <p>{stepFiveData.noteBody}</p>
          </div>

          <button type="button" className="yd-continue" disabled={!canContinue} onClick={handleContinue}>
            {stepFiveData.ctaLabel}
            <ArrowRightIcon size={16} />
          </button>
          {!canContinue && <p className="yd-hint">{hint}</p>}
        </div>
      </main>
      </div>
    </>
  )
}
