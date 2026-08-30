import '../styles/OnboardingSidebar.css'
import logoEmblem from '../assets/Logo.png'
import { onboardingSteps, sidebarBrand, sidebarStat, sidebarQuote } from '../mockData/onboardingData'
import { CheckIcon } from './icons'

// Dark left-hand panel shared by every step of the onboarding wizard: brand
// lockup, step-by-step progress list, an optional photo panel with a stat
// card and quote, and a progress footer.
//
// `backgroundImage` is optional — falls back to a gradient placeholder until
// the real photo asset is provided. `showPhoto` controls whether the photo
// panel renders at all — only step 1's design includes it.
export default function OnboardingSidebar({ currentStep, backgroundImage, showPhoto = true }) {
  const completedCount = currentStep - 1

  return (
    <aside className={`ob-sidebar ${showPhoto ? '' : 'ob-sidebar--no-photo'}`}>
      <div className="ob-stepper-col">
        <div>
          <div className="ob-brand">
            <span className="ob-brand-mark">
              <img src={logoEmblem} alt="CareerTimeMachine emblem" className="ob-brand-emblem" />
            </span>
            <span className="ob-brand-word">CareerTimeMachine</span>
          </div>
          <p className="ob-brand-tagline">{sidebarBrand.tagline}</p>

          <nav className="ob-stepper" aria-label="Onboarding progress">
            {onboardingSteps.map((step) => {
              const isActive = step.id === currentStep
              const isDone = step.id < currentStep
              return (
                <div
                  key={step.id}
                  className={`ob-step ${isActive ? 'ob-step--active' : ''} ${isDone ? 'ob-step--done' : ''}`}
                >
                  <span className="ob-step-index">
                    {isDone ? <CheckIcon size={12} /> : String(step.id).padStart(2, '0')}
                  </span>
                  <span className="ob-step-text">
                    <span className="ob-step-title">{step.title}</span>
                    <span className="ob-step-subtitle">{step.subtitle}</span>
                  </span>
                </div>
              )
            })}
          </nav>
        </div>

        <div className="ob-progress">
          <div className="ob-progress-header">
            <span>Journey progress</span>
            <span>{completedCount}/{onboardingSteps.length}</span>
          </div>
          <div className="ob-progress-bars">
            {onboardingSteps.map((step) => (
              <span
                key={step.id}
                className={`ob-progress-bar ${step.id <= completedCount ? 'ob-progress-bar--filled' : ''}`}
              />
            ))}
          </div>
        </div>
      </div>

      {showPhoto && (
        <div className="ob-photo-col">
          <div
            className="ob-photo-image"
            style={backgroundImage ? { backgroundImage: `url(${backgroundImage})` } : undefined}
          />
          <div className="ob-photo-scrim" />
          <div className="ob-photo-stat">
            <span className="ob-photo-stat-label">{sidebarStat.label}</span>
            <span className="ob-photo-stat-value">{sidebarStat.value}</span>
            <span className="ob-photo-stat-caption">{sidebarStat.caption}</span>
          </div>
          <div className="ob-photo-quote">&ldquo;{sidebarQuote}&rdquo;</div>
        </div>
      )}
    </aside>
  )
}
