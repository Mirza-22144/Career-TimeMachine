import { useEffect, useState } from 'react'
import '../styles/CareerJourney.css'
import { api } from '../api.js'
import { navigate } from '../navigate.js'
import { CheckIcon } from '../components/icons'

// Adds an "s" to a word when the count is more than one. Used to build the
// "skills"/"years" text shown on this screen.
const plural = (n, word) => (n === 1 ? `${n} ${word}` : `${n} ${word}s`)

// One row of the timeline: a dot plus a label/text pair. `done` picks the
// filled checkmark dot vs the pending outline; falls back to a muted
// placeholder line when there's nothing to show yet.
function Stage({ label, text, done, breakStage }) {
  return (
    <div className={`cj-stage ${breakStage ? 'cj-stage--break' : ''}`}>
      <span className={`cj-stage-dot ${breakStage ? 'cj-stage-dot--break' : done ? '' : 'cj-stage-dot--pending'}`}>
        {breakStage ? '◐' : done ? <CheckIcon size={12} color="#FFFFFF" /> : '•'}
      </span>
      <div className="cj-stage-body">
        <span className="cj-stage-label">{label}</span>
        {text ? <p className="cj-stage-text">{text}</p> : <p className="cj-stage-text cj-stage-text--muted">Not recorded yet.</p>}
      </div>
    </div>
  )
}

// Final screen after the wizard, shown at the "/career-journey" URL.
// Displays the completed journey as a timeline - the wizard steps collect
// each piece, this screen shows them brought together, including the
// return status which is only known once the wizard finishes.
export default function CareerJourney() {
  const [loading, setLoading] = useState(true)
  const [journey, setJourney] = useState(null)
  const [direction, setDirection] = useState(null)
  const [areaLabel, setAreaLabel] = useState(null)

  useEffect(() => {
    async function load() {
      const [journeyData, directionData, careerAreas] = await Promise.all([
        api.getCareerJourney(),
        api.getCareerDirection(),
        api.getCatalogue('career-areas'),
      ])
      setJourney(journeyData)
      setDirection(directionData)
      setAreaLabel(careerAreas.find((a) => a.id === directionData.area_to_explore)?.label)
      setLoading(false)
    }
    load()
  }, [])

  if (loading) return <div className="cj-page" />

  const skillCount = journey.selected_skills.catalogue_skills.length + journey.selected_skills.custom_skills.length
  const allSkills = [...journey.selected_skills.catalogue_skills.map((s) => s.label), ...journey.selected_skills.custom_skills]
  const { career_break: careerBreak } = journey

  let breakText = null
  if (careerBreak.break_started_on) {
    const returnPart = careerBreak.return_date_unsure
      ? 'return date still being decided'
      : `returning ${careerBreak.planned_return_date?.slice(0, 4)}`
    const durationPart = careerBreak.break_duration_months != null
      ? ` · ${plural(Math.round(careerBreak.break_duration_months / 12), 'year')} away`
      : ''
    breakText = `Started ${careerBreak.break_started_on.slice(0, 4)} · ${returnPart}${durationPart}`
  }

  return (
    <div className="cj-page">
      <main className="cj-content">
        <span className="cj-eyebrow">YOUR CAREER JOURNEY</span>
        <h1 className="cj-heading">Here is the journey you have built.</h1>
        <p className="cj-subheading">Every stage below is part of your professional story, including the time you stepped away.</p>

        <div className="cj-timeline">
          <Stage
            label="Professional background"
            done={!!journey.previous_role}
            text={journey.previous_role && `${journey.previous_role.label} · ${journey.years_experience?.label || 'experience not recorded'}`}
          />
          <Stage
            label="Skills you're bringing back"
            done={allSkills.length > 0}
            text={allSkills.length > 0 && `${plural(skillCount, 'skill')}: ${allSkills.join(', ')}`}
          />
          <Stage label="Career break" breakStage text={breakText} />
          <Stage
            label="Current return status"
            done={!!journey.current_return_status}
            text={journey.current_return_status?.label}
          />
        </div>

        {direction?.area_to_explore && (
          <div className="cj-direction-card">
            <span className="cj-direction-label">YOUR CHOSEN DIRECTION</span>
            <p className="cj-direction-text">{areaLabel || direction.area_to_explore}</p>
          </div>
        )}

        <div className="cj-scenario-note">
          <strong>Workplace scenarios are coming soon.</strong>
          <p>This is where you'll be able to practise a realistic scenario for your chosen direction.</p>
        </div>

        <button type="button" className="cj-home-link" onClick={() => navigate('/')}>
          Back to Home
        </button>
      </main>
    </div>
  )
}
