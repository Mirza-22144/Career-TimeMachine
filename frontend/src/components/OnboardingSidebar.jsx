import '../styles/OnboardingSidebar.css'
import { onboardingSteps, sidebarBrand, sidebarNext, sidebarStat, sidebarQuote } from '../mockData/onboardingData'
import { navigate } from '../navigate.js'
import { CheckIcon, ShieldIcon } from './icons'

// Left-hand panel shared by every step of the onboarding wizard, shown
// below the shared TopNav: a step-by-step progress list, what the steps
// lead to, an optional photo panel with a stat card and quote, and a
// progress bar at the bottom.
//
// `backgroundImage` is optional — falls back to a plain gradient until a
// real photo is set. `showPhoto` turns the photo panel on or off — only
// step 1's design shows it.
export default function OnboardingSidebar({ currentStep, backgroundImage, showPhoto = true }) {
  const completedCount = currentStep - 1
  const previousStep = onboardingSteps.find((step) => step.id === currentStep - 1)

  return (
    <aside className={`ob-sidebar ${showPhoto ? '' : 'ob-sidebar--no-photo'}`} data-nav-dark>
      <div className="ob-stepper-col">
        <div>
          <p className="ob-brand-tagline">{sidebarBrand.tagline}</p>

          {previousStep && (
            <button type="button" className="ob-back" onClick={() => navigate(previousStep.path)}>
              ← Back to {previousStep.title}
            </button>
          )}

          <nav className="ob-stepper" aria-label="Onboarding progress">
            {onboardingSteps.map((step) => {
              const isActive = step.id === currentStep
              const isDone = step.id < currentStep
              const Tag = isDone ? 'button' : 'div'
              return (
                <Tag
                  key={step.id}
                  type={isDone ? 'button' : undefined}
                  className={`ob-step ${isActive ? 'ob-step--active' : ''} ${isDone ? 'ob-step--done' : ''}`}
                  onClick={isDone ? () => navigate(step.path) : undefined}
                >
                  <span className="ob-step-index">
                    {isDone ? <CheckIcon size={12} /> : String(step.id).padStart(2, '0')}
                  </span>
                  <span className="ob-step-text">
                    <span className="ob-step-title">{step.title}</span>
                    <span className="ob-step-subtitle">{step.subtitle}</span>
                  </span>
                </Tag>
              )
            })}
          </nav>

          <section className="ob-next" aria-label="What happens after these steps">
            <span className="ob-next-label">{sidebarNext.label}</span>
            <ul className="ob-next-list">
              {sidebarNext.items.map((item) => (
                <li key={item.id} className="ob-next-item">
                  <span className="ob-next-title">{item.title}</span>
                  <span className="ob-next-text">{item.text}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>

        <p className="ob-note">
          <ShieldIcon size={14} color="#c4b5fd" />
          <span>{sidebarNext.note}</span>
        </p>

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
