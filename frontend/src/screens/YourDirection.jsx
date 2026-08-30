import { useEffect, useState } from 'react'
import '../styles/YourDirection.css'
import OnboardingSidebar from '../components/OnboardingSidebar'
import { stepFiveData, paceCaptions } from '../mockData/onboardingData'
import { api } from '../api.js'
import { CheckIcon, ArrowRightIcon } from '../components/icons'

const plural = (n, word) => {
  if (n === 1) return `${n} ${word}`
  return `${n} ${word.endsWith('y') ? word.slice(0, -1) + 'ies' : word + 's'}`
}

export default function YourDirection() {
  const [loading, setLoading] = useState(true)
  const [journey, setJourney] = useState(null)
  const [returnStatuses, setReturnStatuses] = useState([])
  const [careerAreas, setCareerAreas] = useState([])
  const [pace, setPace] = useState(null)
  const [areaId, setAreaId] = useState(null)

  useEffect(() => {
    async function load() {
      const [journeyData, statuses, areas, direction] = await Promise.all([
        api.getCareerJourney(),
        api.getCatalogue('return-statuses'),
        api.getCatalogue('career-areas'),
        api.getCareerDirection(),
      ])
      setJourney(journeyData)
      setReturnStatuses(statuses)
      setCareerAreas(areas)
      setPace(direction.return_readiness)
      setAreaId(direction.area_to_explore)
      setLoading(false)
    }
    load()
  }, [])

  const canContinue = !!pace && !!areaId

  const handleContinue = async () => {
    await api.patchCareerDirection({ return_readiness: pace, area_to_explore: areaId })
  }

  if (loading) return <div className="yd-page" />

  const skillCount = journey.selected_skills.catalogue_skills.length + journey.selected_skills.custom_skills.length
  const journeySteps = [
    { label: 'Your Story', caption: journey.previous_role ? `${journey.previous_role.label}, ${journey.years_experience.label}` : '—' },
    { label: 'Your Experience', caption: `${plural(skillCount, 'skill')}` },
    {
      label: 'Your Break',
      caption: journey.career_break.break_started_on
        ? `${journey.career_break.break_started_on.slice(0, 4)} to ${journey.career_break.return_date_unsure ? 'undecided' : journey.career_break.planned_return_date?.slice(0, 4)}`
        : '—',
    },
  ]

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

          <h2 className="yd-question-label">{stepFiveData.areaQuestion}</h2>
          <p className="yd-question-subtext">{stepFiveData.areaSubtext}</p>
          <div className="yd-radio-grid">
            {careerAreas.map((area) => {
              const isActive = areaId === area.id
              return (
                <button
                  type="button"
                  key={area.id}
                  className={`yd-radio ${isActive ? 'yd-radio--active' : ''}`}
                  onClick={() => setAreaId(area.id)}
                >
                  <span className={`yd-radio-dot ${isActive ? 'yd-radio-dot--active' : ''}`} />
                  {area.label}
                </button>
              )
            })}
          </div>

          <div className="yd-note">
            <strong>{stepFiveData.noteTitle}</strong>
            <p>{stepFiveData.noteBody}</p>
          </div>

          <button type="button" className="yd-continue" disabled={!canContinue} onClick={handleContinue}>
            {stepFiveData.ctaLabel}
            <ArrowRightIcon size={16} />
          </button>
        </div>
      </main>
    </div>
  )
}
