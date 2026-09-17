import { useEffect, useState } from 'react'
import '../styles/CareerJourney.css'
import TopNav from '../components/TopNav'
import { api, ApiError } from '../api.js'
import { navigate } from '../navigate.js'
import { consumeJustReturned } from '../accessToken.js'
import { setEditReturn } from '../editReturn.js'
import { getResumeStep } from '../resumeStep.js'

// One row of the four-step journey timeline: a numbered badge, a title,
// a value line, a caption, and an action button (Edit for steps the user
// can still change, View for the read-only Skill Relevance Map).
function JourneyStep({ number, title, value, caption, actionLabel, onAction }) {
  return (
    <div className="cj-step">
      <span className="cj-step-badge">{number}</span>
      <div className="cj-step-body">
        <span className="cj-step-title">{title}</span>
        <p className="cj-step-value">{value || 'Not recorded yet.'}</p>
        <p className="cj-step-caption">{caption}</p>
      </div>
      <button type="button" className="cj-step-action" onClick={onAction}>
        {actionLabel} <span aria-hidden="true">›</span>
      </button>
    </div>
  )
}

// Career Journey summary, shown at the "/career-journey" URL - reached via
// the nav at any time (e.g. stepping away from a Workplace Scenario to fix
// something), or right after entering a valid existing token, in which
// case the heading briefly says "Welcome back" instead (AC 3.1.5/3.2.1).
export default function CareerJourney() {
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)
  const [journey, setJourney] = useState(null)
  const [practiceRole, setPracticeRole] = useState(null)
  const [responsibilityLabels, setResponsibilityLabels] = useState([])
  const [breakReasonLabel, setBreakReasonLabel] = useState(null)
  const [translation, setTranslation] = useState(null)
  // Read once on mount, not on every visit via the nav - only true right
  // after AccessTokenModal validates an existing token.
  const [justReturned] = useState(() => consumeJustReturned())

  const load = async () => {
    try {
      const [journeyData, practiceRoleData, profileData, responsibilities, breakReasons, translationData] =
        await Promise.all([
          api.getCareerJourney(),
          api.getPracticeRole(),
          api.getProfile(),
          api.getCatalogue('responsibilities'),
          api.getCatalogue('break-reasons'),
          api.getCareerTranslation(),
        ])
      setJourney(journeyData)
      setPracticeRole(practiceRoleData)
      setResponsibilityLabels(
        [
          ...profileData.responsibility_ids.map((id) => responsibilities.find((r) => r.id === id)?.label || id),
          ...profileData.custom_responsibilities,
        ],
      )
      setBreakReasonLabel(
        profileData.break_reason === 'other'
          ? profileData.break_reason_other_text
          : breakReasons.find((r) => r.id === profileData.break_reason)?.label,
      )
      setTranslation(translationData)
      setLoading(false)
    } catch (err) {
      // A token can be active with no confirmed profile yet (e.g. she left
      // partway through the wizard) - Career Journey requires a confirmed
      // profile (409) to load at all. That's not a real load failure, it
      // just means there's nothing to show here yet - send her back into
      // the wizard at whichever step is actually still incomplete, not
      // always Step 1, so already-filled steps aren't repeated.
      if (err instanceof ApiError && err.code === 'HTTP_409') {
        try {
          navigate(getResumeStep(await api.getProfile()))
        } catch {
          navigate('/your-story')
        }
        return
      }
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

  if (loading) return (
    <>
      <TopNav />
      <div className="cj-page" />
    </>
  )

  if (loadError) return (
    <>
      <TopNav />
      <div className="cj-page">
        <div className="cj-load-error">
          <p>We couldn&rsquo;t load your saved information. Please try again.</p>
          <button type="button" onClick={retryLoad}>Try Again</button>
        </div>
      </div>
    </>
  )

  const allSkills = [...journey.selected_skills.catalogue_skills.map((s) => s.label), ...journey.selected_skills.custom_skills]

  const { career_break: careerBreak } = journey
  let breakValue = null
  if (careerBreak.break_started_on) {
    const startYear = careerBreak.break_started_on.slice(0, 4)
    const endYear = careerBreak.return_date_unsure ? 'undecided' : careerBreak.planned_return_date?.slice(0, 4)
    const durationPart = careerBreak.break_duration_months != null
      ? ` · ${Math.round(careerBreak.break_duration_months / 12)} years away`
      : ''
    breakValue = `${startYear} to ${endYear}${durationPart}`
  }

  const ownedCount = translation.owned_skills.length + translation.custom_skills.length
  const newHorizonsCount = translation.new_horizons.length

  return (
    <>
      <TopNav />
      <div className="cj-page">
        <main className="cj-content">
          <h1 className="cj-heading">{justReturned ? 'Welcome back' : 'Your Career Journey'}</h1>
          <p className="cj-subheading">
            Here&rsquo;s the journey you&rsquo;ve built so far. Everything is saved and ready when you are.
          </p>

          <div className="cj-timeline">
            <JourneyStep
              number="01"
              title="Your Story"
              value={journey.previous_role && `${journey.previous_role.label} · ${journey.years_experience?.label || ''}`}
              caption="Where your professional story started"
              actionLabel="Edit"
              onAction={() => { setEditReturn(); navigate('/your-story') }}
            />
            <JourneyStep
              number="02"
              title="Your Experience"
              value={allSkills.length > 0 ? allSkills.join(' · ') : null}
              caption={responsibilityLabels.length > 0 ? responsibilityLabels.join(' · ') : 'No responsibilities recorded yet.'}
              actionLabel="Edit"
              onAction={() => { setEditReturn(); navigate('/your-experience') }}
            />
            <JourneyStep
              number="03"
              title="Your Break"
              value={breakValue}
              caption={breakReasonLabel || 'No reason shared.'}
              actionLabel="Edit"
              onAction={() => { setEditReturn(); navigate('/your-break') }}
            />
            <JourneyStep
              number="04"
              title="Skill Relevance Map"
              value={`${ownedCount} skills you keep · ${newHorizonsCount} worth exploring`}
              caption="What your field values now, based on what you already have"
              actionLabel="View"
              onAction={() => navigate('/skill-relevance-map')}
            />
            <JourneyStep
              number="05"
              title="Practice Role"
              value={practiceRole?.role_label || null}
              caption={
                practiceRole?.source === 'predicted'
                  ? 'AI-predicted future role'
                  : practiceRole?.source === 'previous'
                    ? 'Your previous role'
                    : 'Choose which role to practise with'
              }
              actionLabel="Edit"
              onAction={() => navigate('/your-direction')}
            />
          </div>

          <div className="cj-continue-row">
            <button type="button" className="cj-continue" onClick={() => navigate('/workplace-scenario')}>
              Continue your journey <span aria-hidden="true">→</span>
            </button>
            <span className="cj-continue-note">Or edit any stage above. Nothing is locked in.</span>
          </div>
        </main>
      </div>
    </>
  )
}
