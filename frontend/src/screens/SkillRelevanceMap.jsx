import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import '../styles/SkillRelevanceMap.css'
import OnboardingSidebar from '../components/OnboardingSidebar'
import { stepFourData } from '../mockData/onboardingData'
import { api } from '../api.js'
import { navigate } from '../navigate.js'
import { ArrowRightIcon } from '../components/icons'

// Draws a line from each pill to the center card, measured from actual
// rendered positions (works for any number of skill/area pills).
function useFanLines(containerRef, deps) {
  const [state, setState] = useState({ lines: [], top: null, bottom: null })

  useLayoutEffect(() => {
    const map = containerRef.current
    const center = map?.querySelector('.srm-center-card')
    if (!map || !center) return

    const measure = () => {
      const base = map.getBoundingClientRect()
      const anchor = (el, atTop) => {
        const r = el.getBoundingClientRect()
        return { x: r.left + r.width / 2 - base.left, y: (atTop ? r.top : r.bottom) - base.top }
      }
      const top = anchor(center, true)
      const bottom = anchor(center, false)
      const lines = []
      map.querySelectorAll('.srm-horizon-pill').forEach((el) =>
        lines.push({ ...anchor(el, false), tx: top.x, ty: top.y, color: '#14b8a6', type: 'area', name: el.dataset.name }),
      )
      map.querySelectorAll('.srm-skill-pill').forEach((el) =>
        lines.push({ ...anchor(el, true), tx: bottom.x, ty: bottom.y, color: '#7c3aed', type: 'skill', name: el.dataset.name }),
      )
      setState({ lines, top, bottom })
    }

    measure()
    const retry = setTimeout(measure, 300) // catches late web-font reflow
    window.addEventListener('resize', measure)
    return () => {
      clearTimeout(retry)
      window.removeEventListener('resize', measure)
    }
  }, deps)

  return state
}

export default function SkillRelevanceMap() {
  const [loading, setLoading] = useState(true)
  const [journey, setJourney] = useState(null)
  const [translations, setTranslations] = useState([])
  const [active, setActive] = useState(null)
  const mapRef = useRef(null)

  useEffect(() => {
    async function load() {
      const [journeyData, translationData] = await Promise.all([api.getCareerJourney(), api.getCareerTranslation()])
      setJourney(journeyData)
      setTranslations(translationData)
      const firstSkill = journeyData.selected_skills.catalogue_skills[0]?.label || journeyData.selected_skills.custom_skills[0]
      if (firstSkill) setActive({ type: 'skill', name: firstSkill })
      setLoading(false)
    }
    load()
  }, [])

  const { lines, top, bottom } = useFanLines(mapRef, [translations.length])

  if (loading) return <div className="srm-page" />

  const skills = [
    ...journey.selected_skills.catalogue_skills.map((s) => s.label),
    ...journey.selected_skills.custom_skills,
  ]
  const areaNames = [...new Set(translations.flatMap((t) => t.connected_areas.map((a) => a.name)))]

  const findTranslation = (skillName) => translations.find((t) => t.previous_skill.name === skillName)
  const skillsForArea = (areaName) =>
    translations.filter((t) => t.connected_areas.some((a) => a.name === areaName)).map((t) => t.previous_skill.name)

  return (
    <div className="srm-page">
      <OnboardingSidebar currentStep={4} showPhoto={false} />

      <main className="srm-form-panel">
        <div className="srm-content">
          <span className="srm-eyebrow">{stepFourData.eyebrow}</span>
          <h1 className="srm-heading">{stepFourData.heading}</h1>
          <p className="srm-subheading">{stepFourData.subheading}</p>

          <div className="srm-map">
            <div className="srm-map-main" ref={mapRef}>
              <span className="srm-section-label srm-section-label--horizons">{stepFourData.areasLabel}</span>
              {areaNames.length === 0 && <p className="srm-map-message">{stepFourData.noAreasMessage}</p>}
              {areaNames.length > 0 && (
                <div className="srm-pill-row">
                  {areaNames.map((name) => (
                    <button
                      type="button"
                      key={name}
                      data-name={name}
                      className={`srm-horizon-pill ${active?.name === name ? 'srm-horizon-pill--active' : ''}`}
                      onClick={() => setActive({ type: 'area', name })}
                    >
                      ○ {name}
                    </button>
                  ))}
                </div>
              )}

              <svg className="srm-lines">
                {lines.map((l, i) => {
                  const isActive = active?.type === l.type && active?.name === l.name
                  return (
                    <line
                      key={i}
                      x1={l.x}
                      y1={l.y}
                      x2={l.tx}
                      y2={l.ty}
                      stroke={l.color}
                      strokeOpacity={isActive ? 0.9 : 0.35}
                      strokeWidth={isActive ? 2 : 1}
                    />
                  )
                })}
                {top && <circle cx={top.x} cy={top.y} r="4" fill="#0d1628" stroke="#14b8a6" strokeWidth="1.5" />}
                {bottom && <circle cx={bottom.x} cy={bottom.y} r="4" fill="#7c3aed" />}
              </svg>

              <div className="srm-center-card">
                <span className="srm-center-eyebrow">YOU ARE HERE</span>
                <span className="srm-center-role">{journey.previous_role?.label || 'Your role'}</span>
                <span className="srm-center-years">{journey.years_experience?.label}</span>
              </div>

              <div className="srm-pill-row">
                {skills.map((name) => (
                  <button
                    type="button"
                    key={name}
                    data-name={name}
                    className={`srm-skill-pill ${active?.name === name ? 'srm-skill-pill--active' : ''}`}
                    onClick={() => setActive({ type: 'skill', name })}
                  >
                    ● {name}
                  </button>
                ))}
              </div>
              {skills.length > 0 && <p className="srm-relevant-tag">✓ {stepFourData.ownedSummary}</p>}
              <span className="srm-section-label srm-section-label--skills">{stepFourData.ownedLabel}</span>
            </div>

            {active?.type === 'skill' && (
              <div className="srm-detail-card">
                <span className="srm-detail-eyebrow">{stepFourData.ownedLabel}</span>
                <h3 className="srm-detail-title">{active.name}</h3>
                <hr className="srm-detail-divider" />
                {(() => {
                  const t = findTranslation(active.name)
                  const areas = t?.connected_areas || []
                  return areas.length > 0 ? (
                    areas.map((a) => (
                      <p key={a.id} className="srm-detail-note">Connects to: {a.name}</p>
                    ))
                  ) : (
                    <p className="srm-detail-note">{stepFourData.skillNoAreaNote}</p>
                  )
                })()}
              </div>
            )}

            {active?.type === 'area' && (
              <div className="srm-detail-card">
                <span className="srm-detail-eyebrow srm-detail-eyebrow--new">{stepFourData.areasLabel}</span>
                <h3 className="srm-detail-title">{active.name}</h3>
                <hr className="srm-detail-divider" />
                <p className="srm-detail-note">Skills that connect here:</p>
                {skillsForArea(active.name).map((name) => (
                  <p key={name} className="srm-detail-note">● {name}</p>
                ))}
              </div>
            )}
          </div>

          <button
            type="button"
            className="srm-continue"
            onClick={() => navigate('/your-direction')}
          >
            {stepFourData.ctaLabel}
            <ArrowRightIcon size={16} />
          </button>
        </div>
      </main>
    </div>
  )
}
