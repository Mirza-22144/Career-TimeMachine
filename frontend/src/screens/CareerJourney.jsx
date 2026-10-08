import { useEffect, useState } from 'react'
import '../styles/CareerJourney.css'
import TopNav from '../components/TopNav'
import ClearJourneyDialog from '../components/ClearJourneyDialog'
import { ArrowRightIcon } from '../components/icons'
import { api, ApiError } from '../api.js'
import { navigate } from '../navigate.js'
import { setEditReturn } from '../editReturn.js'
import { getResumeStep } from '../resumeStep.js'

// One row of the journey timeline: a numbered badge, a title, a value
// line, a caption, and an Edit button back into that wizard step.
function JourneyStep({ number, title, value, caption, onEdit }) {
  return (
    <div className="cj-step">
      <span className="cj-step-badge">{number}</span>
      <div className="cj-step-body">
        <span className="cj-step-title">{title}</span>
        <p className="cj-step-value">{value || 'Not recorded yet.'}</p>
        <p className="cj-step-caption">{caption}</p>
      </div>
      <button type="button" className="cj-step-action" onClick={onEdit}>
        Edit <span aria-hidden="true">›</span>
      </button>
    </div>
  )
}

// Career Profile, shown at "/career-journey" - reached from the profile
// icon dropdown (AC 3.1.7) or right after entering a valid existing token.
// Iteration 3 trims this to the three profile steps: the Skill Relevance
// Map and Practice Role rows moved to Your Roadmap / Choose Your Path.
export default function CareerJourney() {
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)
  const [journey, setJourney] = useState(null)
  const [responsibilityLabels, setResponsibilityLabels] = useState([])
  // AC 3.5.2: Clear My Journey.
  const [isClearDialogOpen, setIsClearDialogOpen] = useState(false)
  const [isClearing, setIsClearing] = useState(false)
  const [clearError, setClearError] = useState('')

  const load = async () => {
    try {
      const [journeyData, profileData, responsibilities] = await Promise.all([
        api.getCareerJourney(),
        api.getProfile(),
        api.getCatalogue('responsibilities'),
      ])
      setJourney(journeyData)
      setResponsibilityLabels([
        ...profileData.responsibility_ids.map((id) => responsibilities.find((r) => r.id === id)?.label || id),
        ...profileData.custom_responsibilities,
      ])
      setLoading(false)
    } catch (err) {
      // A token with no confirmed profile yet (409) has nothing to show
      // here - send her back into the wizard at the first unfinished step.
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

  const handleClear = async () => {
    setIsClearing(true)
    setClearError('')
    try {
      await api.clearJourney()
      navigate('/')
    } catch {
      // The token is only forgotten locally after a successful delete, so
      // a failure here leaves it active, as the AC requires.
      setClearError("We couldn't clear your journey. Please try again.")
      setIsClearing(false)
    }
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
  let breakCaption = 'Return date to be decided'
  if (careerBreak.break_started_on) {
    const startYear = careerBreak.break_started_on.slice(0, 4)
    const endYear = careerBreak.return_date_unsure ? null : careerBreak.planned_return_date?.slice(0, 4)
    if (endYear) {
      const years = Number(endYear) - Number(startYear)
      breakValue = `${startYear} to ${endYear} · ${years} ${years === 1 ? 'year' : 'years'} away`
      breakCaption = `Planning to return in ${endYear}`
    } else {
      breakValue = `Started ${startYear}`
    }
  }

  return (
    <>
      <TopNav />
      <div className="cj-page">
        <main className="cj-content">
          <h1 className="cj-heading">Your Career Journey</h1>
          <p className="cj-subheading">
            Here&rsquo;s the journey you&rsquo;ve built so far. Everything is saved and ready when you are.
          </p>

          <div className="cj-timeline">
            <JourneyStep
              number="01"
              title="Your Story"
              value={journey.previous_role && `${journey.previous_role.label} · ${journey.years_experience?.label || ''} in IT`}
              caption="Where your professional story started"
              onEdit={() => { setEditReturn(); navigate('/your-story') }}
            />
            <JourneyStep
              number="02"
              title="Your Experience"
              value={allSkills.length > 0 ? allSkills.join(' · ') : null}
              caption={responsibilityLabels.length > 0 ? responsibilityLabels.join(' · ') : 'No responsibilities recorded yet.'}
              onEdit={() => { setEditReturn(); navigate('/your-experience') }}
            />
            <JourneyStep
              number="03"
              title="Your Break"
              value={breakValue}
              caption={breakCaption}
              onEdit={() => { setEditReturn(); navigate('/your-break') }}
            />
          </div>

          <div className="cj-continue-row">
            <button type="button" className="cj-continue" onClick={() => navigate('/choose-your-path')}>
              Continue your journey <ArrowRightIcon size={16} />
            </button>
            <span className="cj-continue-note">Or edit any stage above. Nothing is locked in.</span>
            <button type="button" className="cj-clear" onClick={() => { setClearError(''); setIsClearDialogOpen(true) }}>
              Clear My Journey
            </button>
          </div>
        </main>
      </div>

      {isClearDialogOpen && (
        <ClearJourneyDialog
          onClear={handleClear}
          onCancel={() => setIsClearDialogOpen(false)}
          isClearing={isClearing}
          error={clearError}
        />
      )}
    </>
  )
}
