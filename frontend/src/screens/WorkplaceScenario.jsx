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

// Reached after Your Direction's "Try a Workplace Scenario" (AC 4.1.2/4.1.3),
// or from the nav's Practice Scenarios link once a token is active. Shows
// the practice introduction for whichever role was carried over from Your
// Direction. The actual scenario/question flow is still Iteration 2
// backend/AI work - Continue leads to a placeholder for now.
export default function WorkplaceScenario() {
  const [loading, setLoading] = useState(true)
  // null | 'no-role' | 'intro-failed'
  const [loadError, setLoadError] = useState(null)
  const [role, setRole] = useState(null)
  const [started, setStarted] = useState(false)

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

  if (started) return (
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

          <button type="button" className="ws-intro-continue" onClick={() => setStarted(true)}>
            Continue <span aria-hidden="true">→</span>
          </button>
        </main>
      </div>
    </>
  )
}
