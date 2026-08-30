import { useLayoutEffect, useRef, useState } from 'react'
import '../styles/SkillRelevanceMap.css'
import OnboardingSidebar from '../components/OnboardingSidebar'
import { stepFourData, horizonsByRole } from '../mockData/onboardingData'
import { getOnboardingProfile, saveOnboardingProfile } from '../onboardingState.js'
import { navigate } from '../navigate.js'
import { ArrowRightIcon } from '../components/icons'

// Draws a line from each pill to the center card, measured from actual
// rendered positions (works for any number of horizon/skill pills).
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
        lines.push({ ...anchor(el, false), tx: top.x, ty: top.y, color: '#14b8a6', type: 'new', name: el.dataset.name }),
      )
      map.querySelectorAll('.srm-skill-pill').forEach((el) =>
        lines.push({ ...anchor(el, true), tx: bottom.x, ty: bottom.y, color: '#7c3aed', type: 'owned', name: el.dataset.name }),
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
  const [profile] = useState(getOnboardingProfile)
  const skills = profile.skills || []
  const roleHorizons = horizonsByRole[profile.role]
  // Never suggest a "new" horizon the user already recorded as a skill.
  const horizons = roleHorizons ? roleHorizons.filter((h) => !skills.includes(h)) : []
  const isAligned = !!roleHorizons && horizons.length === 0

  const [active, setActive] = useState(skills[0] ? { type: 'owned', name: skills[0] } : null)
  const mapRef = useRef(null)
  const { lines, top, bottom } = useFanLines(mapRef, [skills.length, horizons.length])

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

              <span className="srm-section-label srm-section-label--horizons">○ NEW HORIZONS</span>
              {!roleHorizons && <p className="srm-map-message">{stepFourData.unavailableMessage}</p>}
              {isAligned && <p className="srm-map-message">{stepFourData.alignedMessage}</p>}
              {horizons.length > 0 && (
                <div className="srm-pill-row">
                  {horizons.map((h) => (
                    <button
                      type="button"
                      key={h}
                      data-name={h}
                      className={`srm-horizon-pill ${active?.name === h ? 'srm-horizon-pill--active' : ''}`}
                      onClick={() => setActive({ type: 'new', name: h })}
                    >
                      ○ {h}
                    </button>
                  ))}
                </div>
              )}

              <div className="srm-center-card">
                <span className="srm-center-eyebrow">YOU ARE HERE</span>
                <span className="srm-center-role">{profile.role || 'Your role'}</span>
                <span className="srm-center-years">
                  {profile.years ? `${profile.years} year${profile.years === 1 ? '' : 's'} experience` : ''}
                </span>
              </div>

              <div className="srm-pill-row">
                {skills.map((s) => (
                  <button
                    type="button"
                    key={s}
                    data-name={s}
                    className={`srm-skill-pill ${active?.name === s ? 'srm-skill-pill--active' : ''}`}
                    onClick={() => setActive({ type: 'owned', name: s })}
                  >
                    ● {s}
                  </button>
                ))}
              </div>
              {skills.length > 0 && <p className="srm-relevant-tag">✓ {stepFourData.ownedSummary}</p>}
              <span className="srm-section-label srm-section-label--skills">● SKILLS YOU BRING BACK</span>
            </div>

            {active && (
              <div className="srm-detail-card">
                <span className={`srm-detail-eyebrow ${active.type === 'new' ? 'srm-detail-eyebrow--new' : ''}`}>
                  {active.type === 'new' ? '○ NEW HORIZONS' : '● SKILLS YOU BRING BACK'}
                </span>
                <h3 className="srm-detail-title">{active.name}</h3>
                <hr className="srm-detail-divider" />
                <p className="srm-detail-note">
                  {profile.role ? stepFourData.relevanceNote(profile.role) : 'Currently in demand for this role.'}
                </p>
                <p className="srm-detail-note">{active.type === 'new' ? stepFourData.newNote : stepFourData.ownedNote}</p>
              </div>
            )}
          </div>

          <button
            type="button"
            className="srm-continue"
            onClick={() => {
              saveOnboardingProfile({ focusSkill: active?.name })
              navigate('/your-direction')
            }}
          >
            {stepFourData.ctaLabel}
            <ArrowRightIcon size={16} />
          </button>
        </div>
      </main>
    </div>
  )
}
