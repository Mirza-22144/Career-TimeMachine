import { useEffect, useState } from 'react'
import '../styles/CareerJourney.css'
import { api } from '../api.js'
import { navigate } from '../navigate.js'
import { CheckIcon } from '../components/icons'

const plural = (n, word) => (n === 1 ? `${n} ${word}` : `${n} ${word}s`)

// AC 2.1.1: displays the full career journey as a chronological timeline -
// previous role, years of experience, career break and current return
// status - built from the real backend, distinct from the wizard steps
// that collected each piece.
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

  return (
    <div className="cj-page">
      <main className="cj-content">
        <span className="cj-eyebrow">YOUR CAREER JOURNEY</span>
        <h1 className="cj-heading">Here is the journey you have built.</h1>
        <p className="cj-subheading">Every stage below is part of your professional story, including the time you stepped away.</p>

        <div className="cj-timeline">
          <div className="cj-stage">
            <span className="cj-stage-dot"><CheckIcon size={12} color="#FFFFFF" /></span>
            <div className="cj-stage-body">
              <span className="cj-stage-label">Professional background</span>
              {journey.previous_role ? (
                <p className="cj-stage-text">{journey.previous_role.label} · {journey.years_experience?.label || 'experience not recorded'}</p>
              ) : (
                <p className="cj-stage-text cj-stage-text--muted">Not recorded yet.</p>
              )}
            </div>
          </div>

          <div className="cj-stage">
            <span className="cj-stage-dot"><CheckIcon size={12} color="#FFFFFF" /></span>
            <div className="cj-stage-body">
              <span className="cj-stage-label">Skills you're bringing back</span>
              {allSkills.length > 0 ? (
                <p className="cj-stage-text">{plural(skillCount, 'skill')}: {allSkills.join(', ')}</p>
              ) : (
                <p className="cj-stage-text cj-stage-text--muted">No skills recorded yet.</p>
              )}
            </div>
          </div>

          <div className="cj-stage cj-stage--break">
            <span className="cj-stage-dot cj-stage-dot--break">◐</span>
            <div className="cj-stage-body">
              <span className="cj-stage-label">Career break</span>
              {careerBreak.break_started_on ? (
                <p className="cj-stage-text">
                  Started {careerBreak.break_started_on.slice(0, 4)}
                  {careerBreak.return_date_unsure
                    ? ' · return date still being decided'
                    : ` · returning ${careerBreak.planned_return_date?.slice(0, 4)}`}
                  {careerBreak.break_duration_months != null && ` · ${plural(Math.round(careerBreak.break_duration_months / 12), 'year')} away`}
                </p>
              ) : (
                <p className="cj-stage-text cj-stage-text--muted">Not recorded yet.</p>
              )}
            </div>
          </div>

          <div className="cj-stage">
            <span className={`cj-stage-dot ${journey.current_return_status ? '' : 'cj-stage-dot--pending'}`}>
              {journey.current_return_status ? <CheckIcon size={12} color="#FFFFFF" /> : '•'}
            </span>
            <div className="cj-stage-body">
              <span className="cj-stage-label">Current return status</span>
              {journey.current_return_status ? (
                <p className="cj-stage-text">{journey.current_return_status.label}</p>
              ) : (
                <p className="cj-stage-text cj-stage-text--muted">Not recorded yet.</p>
              )}
            </div>
          </div>
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
