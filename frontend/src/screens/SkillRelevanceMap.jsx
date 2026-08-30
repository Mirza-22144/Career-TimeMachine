import { useState } from 'react'
import '../styles/SkillRelevanceMap.css'
import OnboardingSidebar from '../components/OnboardingSidebar'
import { stepFourData } from '../mockData/onboardingData'
import { getOnboardingProfile, saveOnboardingProfile } from '../onboardingState.js'
import { navigate } from '../navigate.js'
import { ArrowRightIcon } from '../components/icons'

export default function SkillRelevanceMap() {
  const [profile] = useState(getOnboardingProfile)
  const skills = profile.skills || []
  const [active, setActive] = useState(skills[0] ? { type: 'owned', name: skills[0] } : null)

  return (
    <div className="srm-page">
      <OnboardingSidebar currentStep={4} showPhoto={false} />

      <main className="srm-form-panel">
        <div className="srm-content">
          <span className="srm-eyebrow">{stepFourData.eyebrow}</span>
          <h1 className="srm-heading">{stepFourData.heading}</h1>
          <p className="srm-subheading">{stepFourData.subheading}</p>

          <div className="srm-map">
            <div className="srm-map-main">
              <span className="srm-section-label srm-section-label--horizons">○ NEW HORIZONS</span>
              <div className="srm-pill-row">
                {stepFourData.newHorizons.map((h) => (
                  <button
                    type="button"
                    key={h}
                    className={`srm-horizon-pill ${active?.name === h ? 'srm-horizon-pill--active' : ''}`}
                    onClick={() => setActive({ type: 'new', name: h })}
                  >
                    ○ {h}
                  </button>
                ))}
              </div>

              <span className="srm-connector srm-connector--top" />

              <div className="srm-center-card">
                <span className="srm-center-eyebrow">YOU ARE HERE</span>
                <span className="srm-center-role">{profile.role || 'Your role'}</span>
                <span className="srm-center-years">
                  {profile.years ? `${profile.years} year${profile.years === 1 ? '' : 's'} experience` : ''}
                </span>
              </div>

              <span className="srm-connector srm-connector--bottom" />

              <div className="srm-pill-row">
                {skills.map((s) => (
                  <button
                    type="button"
                    key={s}
                    className={`srm-skill-pill ${active?.name === s ? 'srm-skill-pill--active' : ''}`}
                    onClick={() => setActive({ type: 'owned', name: s })}
                  >
                    ● {s}
                  </button>
                ))}
              </div>
              <span className="srm-section-label srm-section-label--skills">● SKILLS YOU BRING BACK</span>
            </div>

            {active && (
              <div className="srm-detail-card">
                <span className={`srm-detail-eyebrow ${active.type === 'new' ? 'srm-detail-eyebrow--new' : ''}`}>
                  {active.type === 'new' ? '○ NEW HORIZONS' : '● SKILLS YOU BRING BACK'}
                </span>
                <h3 className="srm-detail-title">{active.name}</h3>
                <hr className="srm-detail-divider" />
                <p className="srm-detail-note">{stepFourData.relevanceNote}</p>
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
