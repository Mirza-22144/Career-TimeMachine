import { useEffect, useState } from 'react'
import '../styles/WorkplaceScenario.css'
import TopNav from '../components/TopNav'
import { getSelectedRole } from '../practiceSession.js'
import { navigate } from '../navigate.js'

const HOW_IT_WORKS = [
  { number: 1, text: 'Explore your workplace and choose an area.' },
  { number: 2, text: 'Complete a realistic workplace activity or practical task.' },
  { number: 3, text: 'Get feedback on what you did well and what you could explore further.' },
]

// value must match the backend's duration enum (quick/standard/challenge -
// see backend/docs/API-CONTRACT.md); "Extended" is only the on-screen
// label, chosen to avoid duplicating "Challenge" as both a duration and a
// difficulty option (the AC text says "Challenge (15 min)" for duration,
// but the approved Figma design labels it "Extended" instead).
const DURATIONS = [
  { value: 'quick', label: 'Quick', caption: '5 min' },
  { value: 'standard', label: 'Standard', caption: '10 min' },
  { value: 'challenge', label: 'Extended', caption: '15 min' },
]

const DIFFICULTIES = [
  { value: 'guided', label: 'Guided', caption: 'More prompts along the way' },
  { value: 'standard', label: 'Standard', caption: 'Work through it as you would at work' },
  { value: 'challenge', label: 'Challenge', caption: 'Less context, more to weigh up' },
]

// Reached after Your Direction's "Try a Workplace Scenario" (AC 4.1.2/4.1.3),
// or from the nav's Practice Scenarios link once a token is active. Walks
// through the intro (AC 4.2.1) then the time/difficulty setup (AC 4.2.2)
// for whichever role was carried over from Your Direction. The actual
// scenario/question flow is still Iteration 2 backend/AI work.
export default function WorkplaceScenario() {
  const [loading, setLoading] = useState(true)
  // null | 'no-role' | 'intro-failed'
  const [loadError, setLoadError] = useState(null)
  const [role, setRole] = useState(null)
  // 'intro' | 'setup' | 'placeholder'
  const [step, setStep] = useState('intro')
  // Nothing pre-selected - Maya must explicitly choose both.
  const [duration, setDuration] = useState(null)
  const [difficulty, setDifficulty] = useState(null)
  const [attemptedContinue, setAttemptedContinue] = useState(false)

  const load = () => {
    const selected = getSelectedRole()
    if (!selected) {
      setLoadError('no-role')
      setLoading(false)
      return
    }
    try {
      // Mocked "create a practice session" step (AC 4.1.3) - stands in for
      // a real backend session-creation call once BE/AI are ready. Also
      // covers AC 4.2.1's "introduction cannot be loaded" exception, since
      // this is the same load step that prepares the intro screen below.
      setRole(selected)
      setLoadError(null)
      setLoading(false)
    } catch {
      setLoadError('intro-failed')
      setLoading(false)
    }
  }

  useEffect(() => {
    function run() {
      load()
    }
    run()
  }, [])

  const retryLoad = () => {
    setLoading(true)
    load()
  }

  const handleSetupContinue = () => {
    setAttemptedContinue(true)
    if (!duration || !difficulty) return
    setStep('placeholder')
  }

  if (loading) return (
    <>
      <TopNav />
      <div className="ws-page" />
    </>
  )

  if (loadError) return (
    <>
      <TopNav />
      <div className="ws-page">
        <div className="ws-load-error">
          <p>
            {loadError === 'no-role'
              ? "We couldn't load your selected role. Please try again."
              : "We couldn't load your practice introduction. Please try again."}
          </p>
          <button type="button" onClick={retryLoad}>Try Again</button>
          <button type="button" className="ws-load-error-link" onClick={() => navigate('/your-direction')}>
            Back to Your Direction
          </button>
        </div>
      </div>
    </>
  )

  if (step === 'placeholder') return (
    <>
      <TopNav />
      <div className="ws-page">
        <main className="ws-content">
          <span className="ws-eyebrow">WORKPLACE SCENARIO</span>
          <h1 className="ws-heading">Workplace scenarios are coming soon.</h1>
          <p className="ws-subheading">
            This is where you&rsquo;ll practise a realistic scenario for {role.label}.
          </p>
          <button type="button" className="ws-back-link" onClick={() => navigate('/career-journey')}>
            Back to Career Journey
          </button>
        </main>
      </div>
    </>
  )

  if (step === 'setup') return (
    <>
      <TopNav />
      <div className="ws-page">
        <main className="ws-intro-content">
          <h1 className="ws-intro-heading">Set up your practice</h1>
          <p className="ws-intro-subheading">
            Time and challenge are set separately. A shorter session is not an easier one.
          </p>

          <h2 className="ws-setup-label">How much time do you have?</h2>
          <div className="ws-setup-grid">
            {DURATIONS.map((option) => {
              const isActive = duration === option.value
              return (
                <button
                  type="button"
                  key={option.value}
                  className={`ws-setup-card ${isActive ? 'ws-setup-card--active' : ''}`}
                  onClick={() => setDuration(option.value)}
                >
                  <div className="ws-setup-card-header">
                    <strong>{option.label}</strong>
                    <span className={`ws-setup-radio ${isActive ? 'ws-setup-radio--active' : ''}`}>
                      {isActive && <span aria-hidden="true">✓</span>}
                    </span>
                  </div>
                  <span className="ws-setup-caption ws-setup-caption--mono">{option.caption}</span>
                </button>
              )
            })}
          </div>

          <h2 className="ws-setup-label">How challenging would you like it to be?</h2>
          <div className="ws-setup-grid">
            {DIFFICULTIES.map((option) => {
              const isActive = difficulty === option.value
              return (
                <button
                  type="button"
                  key={option.value}
                  className={`ws-setup-card ${isActive ? 'ws-setup-card--active' : ''}`}
                  onClick={() => setDifficulty(option.value)}
                >
                  <div className="ws-setup-card-header">
                    <strong>{option.label}</strong>
                    <span className={`ws-setup-radio ${isActive ? 'ws-setup-radio--active' : ''}`}>
                      {isActive && <span aria-hidden="true">✓</span>}
                    </span>
                  </div>
                  <span className="ws-setup-caption">{option.caption}</span>
                </button>
              )
            })}
          </div>

          <button type="button" className="ws-intro-continue" onClick={handleSetupContinue}>
            Continue <span aria-hidden="true">→</span>
          </button>
          {attemptedContinue && (!duration || !difficulty) && (
            <p className="ws-setup-hint">Choose a practice time and difficulty to continue.</p>
          )}
        </main>
      </div>
    </>
  )

  return (
    <>
      <TopNav />
      <div className="ws-page">
        <main className="ws-intro-content">
          <h1 className="ws-intro-heading">Welcome to your practice area</h1>
          <p className="ws-intro-subheading">
            You&rsquo;ll work through a realistic workplace situation based on your selected role and experience.
          </p>

          <h2 className="ws-intro-label">How it works</h2>
          <div className="ws-intro-steps">
            {HOW_IT_WORKS.map((step) => (
              <div key={step.number} className="ws-intro-step">
                <span className="ws-intro-step-number">{step.number}</span>
                <p>{step.text}</p>
              </div>
            ))}
          </div>

          <hr className="ws-intro-divider" />

          <p className="ws-intro-disclaimer">
            Nothing here is graded. Your practice is designed to help you reconnect with your existing experience
            while exploring what has changed.
          </p>

          <button type="button" className="ws-intro-continue" onClick={() => setStep('setup')}>
            Continue <span aria-hidden="true">→</span>
          </button>
        </main>
      </div>
    </>
  )
}
