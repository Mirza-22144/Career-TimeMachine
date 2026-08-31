import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import '../styles/SkillRelevanceMap.css'
import OnboardingSidebar from '../components/OnboardingSidebar'
import { stepFourData } from '../mockData/onboardingData'
import { api } from '../api.js'
import { navigate } from '../navigate.js'
import { ArrowRightIcon } from '../components/icons'

// Real per-role in-demand skill lists can run long; only the top slice
// shows by default, with a "Show all" control for the rest.
const DEFAULT_HORIZON_COUNT = 12

// Draws a line from each pill to the center card, measured from actual
// rendered positions (works for any number of skill/horizon pills).
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
        lines.push({ ...anchor(el, false), tx: top.x, ty: top.y, color: '#14b8a6', type: 'horizon', name: el.dataset.name }),
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
  const [data, setData] = useState(null)
  const [active, setActive] = useState(null)
  const [showAllHorizons, setShowAllHorizons] = useState(false)
  const mapRef = useRef(null)

  useEffect(() => {
    async function load() {
      const result = await api.getCareerTranslation()
      setData(result)
      const firstOwned = result.owned_skills[0]?.label || result.custom_skills[0]
      if (firstOwned) setActive({ type: 'skill', name: firstOwned })
      setLoading(false)
    }
    load()
  }, [])

  const { lines, top, bottom } = useFanLines(mapRef, [data?.new_horizons.length, data?.owned_skills.length, showAllHorizons])

  if (loading) return <div className="srm-page" />

  const ownedSkills = [
    ...data.owned_skills,
    ...data.custom_skills.map((label) => ({ id: label, label, still_relevant: null, custom: true })),
  ]
  const horizons = data.new_horizons
  const visibleHorizons = showAllHorizons ? horizons : horizons.slice(0, DEFAULT_HORIZON_COUNT)
  const hasMoreHorizons = horizons.length > DEFAULT_HORIZON_COUNT

  const findOwned = (name) => ownedSkills.find((s) => s.label === name)

  return (
    <div className="srm-page">
      <OnboardingSidebar currentStep={4} showPhoto={false} />

      <main className="srm-form-panel">
        <div className="srm-content">
          <span className="srm-eyebrow">{stepFourData.eyebrow}</span>
          <h1 className="srm-heading">{stepFourData.heading}</h1>
          <p className="srm-subheading">{stepFourData.subheading}</p>

          {!data.role_data_available ? (
            <div className="srm-map">
              <p className="srm-map-message">{stepFourData.noRoleDataMessage}</p>
            </div>
          ) : (
            <div className="srm-map">
              <div className="srm-map-main" ref={mapRef}>
                <span className="srm-section-label srm-section-label--horizons">{stepFourData.horizonsLabel}</span>
                {horizons.length === 0 && <p className="srm-map-message">{stepFourData.allAlignedMessage}</p>}
                {horizons.length > 0 && (
                  <>
                    <div className="srm-pill-row">
                      {visibleHorizons.map((skill) => (
                        <button
                          type="button"
                          key={skill.id}
                          data-name={skill.label}
                          className={`srm-horizon-pill ${active?.name === skill.label ? 'srm-horizon-pill--active' : ''}`}
                          onClick={() => setActive({ type: 'horizon', name: skill.label })}
                        >
                          ○ {skill.label}
                        </button>
                      ))}
                    </div>
                    {hasMoreHorizons && (
                      <button
                        type="button"
                        className="srm-show-more"
                        onClick={() => setShowAllHorizons((prev) => !prev)}
                      >
                        {showAllHorizons ? 'Show fewer New Horizons' : `Show all ${horizons.length} New Horizons`}
                      </button>
                    )}
                  </>
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
                  <span className="srm-center-role">{data.role_label}</span>
                </div>

                <div className="srm-pill-row">
                  {ownedSkills.map((skill) => (
                    <button
                      type="button"
                      key={skill.id}
                      data-name={skill.label}
                      className={`srm-skill-pill ${active?.name === skill.label ? 'srm-skill-pill--active' : ''}`}
                      onClick={() => setActive({ type: 'skill', name: skill.label })}
                    >
                      ● {skill.label}
                    </button>
                  ))}
                </div>
                {ownedSkills.length > 0 && <p className="srm-relevant-tag">✓ {stepFourData.ownedSummary}</p>}
                <span className="srm-section-label srm-section-label--skills">{stepFourData.ownedLabel}</span>
              </div>

              {active?.type === 'skill' &&
                (() => {
                  const skill = findOwned(active.name)
                  return (
                    <div className="srm-detail-card">
                      <span className="srm-detail-eyebrow">{stepFourData.ownedLabel}</span>
                      <h3 className="srm-detail-title">{active.name}</h3>
                      <hr className="srm-detail-divider" />
                      {skill?.custom ? (
                        <p className="srm-detail-note">{stepFourData.customSkillNote}</p>
                      ) : skill?.still_relevant ? (
                        <p className="srm-detail-note">✓ {stepFourData.stillRelevantTag}</p>
                      ) : (
                        <p className="srm-detail-note">{stepFourData.notInDemandNote}</p>
                      )}
                    </div>
                  )
                })()}

              {active?.type === 'horizon' && (
                <div className="srm-detail-card">
                  <span className="srm-detail-eyebrow srm-detail-eyebrow--new">{stepFourData.horizonsLabel}</span>
                  <h3 className="srm-detail-title">{active.name}</h3>
                  <hr className="srm-detail-divider" />
                  <p className="srm-detail-note">{stepFourData.horizonNote(data.role_label)}</p>
                </div>
              )}
            </div>
          )}

          <button type="button" className="srm-continue" onClick={() => navigate('/your-direction')}>
            {stepFourData.ctaLabel}
            <ArrowRightIcon size={16} />
          </button>
        </div>
      </main>
    </div>
  )
}
