import { useEffect, useState } from 'react'
import '../styles/WorkplaceScenario.css'
import TopNav from '../components/TopNav'
import workplaceImg from '../assets/workplace.png'
import { WORKPLACE_AREAS, getRelevantAreaIds, getPrimaryAreaId } from '../mockData/workplaceAreas.js'
import {
  UserIcon, BarChartIcon, HeadsetIcon, FileTextIcon, LightbulbIcon, UsersIcon,
  FlaskIcon, CodeIcon, ShieldIcon, GlobeIcon, BellIcon, LayoutIcon, ClockIcon,
} from '../components/icons'
import { api, ApiError } from '../api.js'
import { navigate } from '../navigate.js'

const AREA_ICONS = {
  user: UserIcon,
  barChart: BarChartIcon,
  headset: HeadsetIcon,
  fileText: FileTextIcon,
  lightbulb: LightbulbIcon,
  users: UsersIcon,
  flask: FlaskIcon,
  code: CodeIcon,
  shield: ShieldIcon,
  globe: GlobeIcon,
  bell: BellIcon,
}

const HOW_IT_WORKS = [
  { number: 1, text: 'Explore your workplace and choose an area.' },
  { number: 2, text: 'Complete a realistic workplace activity or practical task.' },
  { number: 3, text: 'Get feedback on what you did well and what you could explore further.' },
]

// Matches the backend's duration enum (quick/standard/challenge - see
// backend/docs/API-CONTRACT.md); "Extended" is only the on-screen label for
// "challenge", chosen to avoid duplicating "Challenge" as both a duration
// and a difficulty option.
const DURATIONS = [
  { value: 'quick', label: 'Quick', caption: '5 min' },
  { value: 'standard', label: 'Standard', caption: '10 min' },
  { value: 'challenge', label: 'Extended', caption: '15 min' },
]

// Labels match AC 4.2.2 ("Easy, Standard, Complex"); values are the
// backend's own guided/standard/challenge enum.
const DIFFICULTIES = [
  { value: 'guided', label: 'Easy', caption: 'More prompts along the way' },
  { value: 'standard', label: 'Standard', caption: 'Work through it as you would at work' },
  { value: 'challenge', label: 'Complex', caption: 'Less context, more to weigh up' },
]

// Reached after Your Direction's "Try a Workplace Scenario" (AC 4.1.2/4.1.3),
// or from the nav's Practice Scenarios link once a token is active. Walks
// through the intro (AC 4.2.1), the time/difficulty setup (AC 4.2.2), the
// prep screen (AC 4.2.3), the interactive workplace (AC 4.3.1-4.3.4), and
// the activity itself (AC 4.4.1-4.4.2, AC 4.5.1-4.5.3) for whichever role
// was saved on Your Direction. Talks to the real backend end to end -
// practice role, session, scenario and feedback all come from
// POST/GET /practice-role and /practice-sessions, not mock data. Sessions
// are still in-memory on the backend (not yet in Postgres - see Cross-team
// blocker B2), so progress does not survive a backend restart yet, but the
// frontend/backend contract itself is real.
export default function WorkplaceScenario() {
  const [loading, setLoading] = useState(true)
  // null | 'no-role' | 'intro-failed' | 'restore-failed'
  const [loadError, setLoadError] = useState(null)
  const [role, setRole] = useState(null)
  // 'intro' | 'setup' | 'prep' | 'workplace' | 'activity' | 'feedback' | 'complete'
  const [step, setStep] = useState('intro')
  // Nothing pre-selected - Maya must explicitly choose both.
  const [duration, setDuration] = useState(null)
  const [difficulty, setDifficulty] = useState(null)
  const [attemptedContinue, setAttemptedContinue] = useState(false)
  // AC 4.2.3 - the prep screen's own data and loading/error state. Starting
  // the real backend session happens here (POST /practice-sessions), since
  // that call is what actually generates the scenario shown on this screen.
  const [prepLoading, setPrepLoading] = useState(false)
  const [prepError, setPrepError] = useState(false)
  const [session, setSession] = useState(null)
  const [newSkillFocus, setNewSkillFocus] = useState(null)
  // AC 4.3.2 - the scenario banner can be hidden/shown, but stays loaded
  // and tied to the session either way.
  const [scenarioVisible, setScenarioVisible] = useState(true)
  // AC 4.3.3 - which hotspot's detail panel is open, if any.
  const [selectedAreaId, setSelectedAreaId] = useState(null)
  // AC 4.4.2 - nothing pre-selected; she must explicitly choose an option.
  const [selectedOptionId, setSelectedOptionId] = useState(null)
  const [submitError, setSubmitError] = useState(false)
  const [showSummaryPlaceholder, setShowSummaryPlaceholder] = useState(false)

  const load = async () => {
    try {
      const practiceRole = await api.getPracticeRole()
      if (!practiceRole.role_id) {
        setLoadError('no-role')
        setLoading(false)
        return
      }
      setRole({ id: practiceRole.role_id, label: practiceRole.role_label, source: practiceRole.source })

      // AC 4.3.4: resume an already-active session (e.g. she left via the
      // nav and came back through "Practice Scenarios") instead of
      // restarting the intro.
      try {
        const current = await api.getCurrentPracticeSession()
        setSession(current)
        setDuration(current.duration)
        setDifficulty(current.difficulty)
        const activeScenario = current.scenarios[0]
        if (current.status === 'completed') setStep('complete')
        else if (activeScenario?.response) setStep('feedback')
        else setStep('workplace')
        setLoadError(null)
        setLoading(false)
        return
      } catch (err) {
        if (!(err instanceof ApiError && err.code === 'PRACTICE_SESSION_NOT_FOUND')) {
          throw err
        }
        // No active session yet - fall through to the intro flow below.
      }

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
    setStep('prep')
    loadPrep()
  }

  // AC 4.2.3: gathers what the prep screen shows - a real, current in-demand
  // skill she hasn't already recorded (GET /career-translation's
  // new_horizons), and starts the real practice session (POST
  // /practice-sessions), which is what actually generates the scenario
  // she'll see. Starting again here (e.g. after changing duration/
  // difficulty) abandons any previous active session, per the backend
  // contract.
  const loadPrep = async () => {
    setPrepLoading(true)
    setPrepError(false)
    try {
      const [translation, newSession] = await Promise.all([
        api.getCareerTranslation(),
        api.startPracticeSession(duration, difficulty),
      ])
      setNewSkillFocus(translation.new_horizons?.[0]?.label || null)
      setSession(newSession)
      setPrepLoading(false)
    } catch {
      setPrepError(true)
      setPrepLoading(false)
    }
  }

  // The session already exists (started during loadPrep) - entering the
  // workplace is just a UI transition, no further backend call needed.
  const handleEnterWorkplace = () => {
    setStep('workplace')
  }

  const handleStartTask = () => {
    setSelectedOptionId(null)
    setSubmitError(false)
    setStep('activity')
  }

  // AC 4.4.2: records her answer and gets reflective feedback back in the
  // same call (AC 4.5.1).
  const handleSubmitActivity = async () => {
    if (!selectedOptionId) return
    setSubmitError(false)
    try {
      const result = await api.submitScenarioResponse(
        session.session_id, activity.scenario_id, { selected_option_id: selectedOptionId },
      )
      setSession((prev) => ({ ...prev, scenarios: [result.scenario], progress: result.progress }))
      setStep('feedback')
    } catch {
      setSubmitError(true)
    }
  }

  // AC 4.5.3: marks the session completed on the backend before showing the
  // completion summary.
  const handleCompletePractice = async () => {
    try {
      const completed = await api.completePracticeSession(session.session_id)
      setSession(completed)
    } catch {
      // Non-critical for what's already been done locally - still show the
      // completion summary from what we already have.
    }
    setStep('complete')
  }

  const handleBackToWorkplace = () => {
    setSelectedAreaId(null)
    setStep('workplace')
  }

  const primaryAreaId = role ? getPrimaryAreaId(role.id) : null
  const difficultyLabel = DIFFICULTIES.find((d) => d.value === difficulty)?.label
  const relevantAreaIds = role ? getRelevantAreaIds(role.id) : new Set()
  const activity = session?.scenarios?.[0] || null
  const isCompleted = activity?.status === 'completed'
  const selectedArea = selectedAreaId ? WORKPLACE_AREAS.find((a) => a.id === selectedAreaId) : null
  const isPrimaryAreaSelected = selectedAreaId && selectedAreaId === primaryAreaId

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
            {loadError === 'no-role' && "We couldn't load your selected role. Please try again."}
            {loadError === 'intro-failed' && "We couldn't load your practice introduction. Please try again."}
            {loadError === 'restore-failed' && "We couldn't restore your practice session. Please try again."}
          </p>
          <button type="button" onClick={retryLoad}>Try Again</button>
          <button type="button" className="ws-load-error-link" onClick={() => navigate('/your-direction')}>
            Back to Your Direction
          </button>
        </div>
      </div>
    </>
  )

  // AC 4.4.1/4.4.2: the activity itself - a single-selection MCQ, nothing
  // pre-selected until she chooses an option.
  if (step === 'activity' && activity) return (
    <>
      <TopNav />
      <div className="ws-activity-page">
        <div className="ws-activity-topbar">
          <button type="button" className="ws-activity-back" onClick={handleBackToWorkplace}>
            <span aria-hidden="true">&larr;</span> Back to workplace
          </button>
          <span className="ws-activity-breadcrumb">
            {role.label} &middot; {selectedArea?.label}
          </span>
        </div>
        <main className="ws-activity-body">
          <div className="ws-activity-main">
            <span className="ws-eyebrow ws-eyebrow--left">PRACTICAL ACTIVITY</span>
            <h1 className="ws-activity-heading">{activity.title}</h1>
            <div className="ws-mcq-card">
              <p className="ws-mcq-question">{activity.task}</p>
              <div className="ws-mcq-options">
                {activity.options.map((option) => {
                  const isSelected = selectedOptionId === option.option_id
                  return (
                    <button
                      type="button"
                      key={option.option_id}
                      className={`ws-mcq-option ${isSelected ? 'ws-mcq-option--selected' : ''}`}
                      onClick={() => setSelectedOptionId(option.option_id)}
                    >
                      <span className={`ws-mcq-radio ${isSelected ? 'ws-mcq-radio--selected' : ''}`}>
                        {isSelected && <span aria-hidden="true">&#10003;</span>}
                      </span>
                      {option.text}
                    </button>
                  )
                })}
              </div>
            </div>
            {submitError && (
              <p className="ws-setup-hint">We couldn&rsquo;t submit your response. Please try again.</p>
            )}
          </div>
          <aside className="ws-activity-side">
            {activity.guidance.length > 0 && (
              <div className="ws-hint-panel">
                <span className="ws-hint-label">
                  <LightbulbIcon size={16} color="#7C3AED" /> Worth remembering
                </span>
                <p>{activity.guidance[0]}</p>
              </div>
            )}
            <button
              type="button"
              className="ws-intro-continue ws-activity-continue"
              disabled={!selectedOptionId}
              onClick={handleSubmitActivity}
            >
              Continue <span aria-hidden="true">→</span>
            </button>
            <button type="button" className="ws-back-link" onClick={handleBackToWorkplace}>
              Back to workplace
            </button>
          </aside>
        </main>
      </div>
    </>
  )

  // AC 4.5.1/4.5.2: reflective feedback plus a skill to explore, shown
  // right after she submits the activity.
  if (step === 'feedback' && activity?.feedback) return (
    <>
      <TopNav />
      <div className="ws-activity-page">
        <div className="ws-activity-topbar">
          <button type="button" className="ws-activity-back" onClick={handleBackToWorkplace}>
            <span aria-hidden="true">&larr;</span> Back to workplace
          </button>
          <span className="ws-activity-breadcrumb">
            {role.label} &middot; {selectedArea?.label}
          </span>
        </div>
        <main className="ws-feedback-body">
          <h1 className="ws-activity-heading">Your practice feedback</h1>
          <div className="ws-feedback-card">
            <div className="ws-feedback-section">
              <span className="ws-feedback-label">
                <span className="ws-feedback-dot ws-feedback-dot--green" aria-hidden="true" /> WHAT WORKED WELL
              </span>
              {activity.feedback.what_worked_well.map((line) => <p key={line}>{line}</p>)}
            </div>
            <hr className="ws-intro-divider" />
            <div className="ws-feedback-section">
              <span className="ws-feedback-label">
                <span className="ws-feedback-dot" aria-hidden="true" /> CONSIDER
              </span>
              {[...activity.feedback.trade_offs, ...activity.feedback.areas_to_consider].map((line) => (
                <p key={line}>{line}</p>
              ))}
            </div>
            {activity.feedback.skill_to_explore && (
              <>
                <hr className="ws-intro-divider" />
                <div className="ws-feedback-section">
                  <span className="ws-feedback-label">
                    <span className="ws-feedback-ring" aria-hidden="true" /> SKILL TO EXPLORE
                  </span>
                  <h3 className="ws-feedback-skill-title">{activity.feedback.skill_to_explore.skill}</h3>
                  <p>{activity.feedback.skill_to_explore.why_relevant}</p>
                </div>
              </>
            )}
          </div>
          <div className="ws-feedback-actions">
            <button type="button" className="ws-intro-continue" onClick={handleCompletePractice}>
              Complete practice <span aria-hidden="true">→</span>
            </button>
            <button type="button" className="ws-back-link" onClick={handleBackToWorkplace}>
              Back to workplace
            </button>
          </div>
        </main>
      </div>
    </>
  )

  // AC 4.5.3: shown once the session's one activity is complete.
  if (step === 'complete') return (
    <>
      <TopNav />
      <div className="ws-page">
        <main className="ws-intro-content">
          <h1 className="ws-intro-heading">Practice complete</h1>
          <p className="ws-intro-subheading">You&rsquo;ve completed the available activities for this practice session.</p>

          <div className="ws-prep-card ws-complete-card">
            <span className="ws-prep-eyebrow">THIS SESSION</span>
            <div className="ws-complete-row">
              <span>Role</span>
              <strong>{role.label}</strong>
            </div>
            <div className="ws-complete-row">
              <span>Focus</span>
              <strong>{activity?.title}</strong>
            </div>
            <div className="ws-complete-row">
              <span>Setup</span>
              <strong>{DURATIONS.find((d) => d.value === duration)?.caption} &middot; {difficultyLabel}</strong>
            </div>
            <div className="ws-complete-row">
              <span>Activities</span>
              <strong>1 of 1 completed</strong>
            </div>
            {activity?.feedback?.skill_to_explore && (
              <>
                <hr className="ws-intro-divider" />
                <span className="ws-prep-eyebrow">SKILL TO EXPLORE</span>
                <h2 className="ws-prep-title">{activity.feedback.skill_to_explore.skill}</h2>
              </>
            )}
          </div>

          {showSummaryPlaceholder && (
            <p className="ws-summary-placeholder">
              <ClockIcon size={16} color="#7C3AED" />
              Practice summary coming soon. This part of the product is not built yet.
            </p>
          )}

          <div className="ws-feedback-actions">
            <button type="button" className="ws-intro-continue" onClick={() => navigate('/career-journey')}>
              Continue <span aria-hidden="true">→</span>
            </button>
            <button type="button" className="ws-back-link" onClick={() => setShowSummaryPlaceholder(true)}>
              Practice summary
            </button>
          </div>
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

  if (step === 'prep' && prepLoading) return (
    <>
      <TopNav />
      <div className="ws-page" />
    </>
  )

  if (step === 'prep' && prepError) return (
    <>
      <TopNav />
      <div className="ws-page">
        <div className="ws-load-error">
          <p>We couldn&rsquo;t prepare your practice. Please try again.</p>
          <button type="button" onClick={loadPrep}>Try Again</button>
        </div>
      </div>
    </>
  )

  if (step === 'prep') return (
    <>
      <TopNav />
      <div className="ws-page">
        <main className="ws-intro-content">
          <h1 className="ws-intro-heading">Your practice</h1>
          <p className="ws-prep-subtitle">{role.label}</p>

          <div className="ws-prep-card">
            <span className="ws-prep-eyebrow">TODAY&rsquo;S FOCUS</span>
            <h2 className="ws-prep-title">{activity.title}</h2>
            <hr className="ws-intro-divider" />

            <span className="ws-prep-eyebrow">YOU&rsquo;LL USE</span>
            <div className="ws-prep-pills">
              {activity.skills_used.map((skill) => (
                <span key={skill} className="ws-prep-pill">{skill}</span>
              ))}
            </div>
            <hr className="ws-intro-divider" />

            <span className="ws-prep-eyebrow">YOU&rsquo;LL PRACTISE</span>
            <p className="ws-prep-task">{activity.task}</p>
            <hr className="ws-intro-divider" />

            {newSkillFocus && (
              <>
                <span className="ws-prep-eyebrow">NEW SKILL TO EXPLORE</span>
                <p className="ws-prep-task">{newSkillFocus}</p>
                <hr className="ws-intro-divider" />
              </>
            )}

            <div className="ws-prep-footer">
              <div>
                <span className="ws-prep-eyebrow">ESTIMATED TIME</span>
                <strong className="ws-prep-footer-value ws-setup-caption--mono">
                  {DURATIONS.find((d) => d.value === duration)?.caption}
                </strong>
              </div>
              <div>
                <span className="ws-prep-eyebrow">DIFFICULTY</span>
                <strong className="ws-prep-footer-value">{difficultyLabel}</strong>
              </div>
            </div>
          </div>

          <button type="button" className="ws-intro-continue" onClick={handleEnterWorkplace}>
            Enter Workplace <span aria-hidden="true">→</span>
          </button>
        </main>
      </div>
    </>
  )

  if (step === 'workplace') return (
    <>
      <TopNav />
      <div className="ws-workplace-page">
        <div className="ws-workplace-header">
          <div className="ws-workplace-header-left">
            <span className="ws-workplace-icon"><LayoutIcon size={18} /></span>
            <div>
              <h1 className="ws-workplace-title">Your Workplace</h1>
              <p className="ws-workplace-subtitle">Explore the areas highlighted for your role.</p>
            </div>
          </div>
          <div className="ws-workplace-header-right">
            <div>
              <span className="ws-prep-eyebrow">SELECTED ROLE</span>
              <strong className="ws-workplace-role">{role.label}</strong>
            </div>
            <div>
              <span className="ws-prep-eyebrow">PRACTICE PROGRESS</span>
              <div className="ws-progress-row">
                <div className="ws-progress-track">
                  <div
                    className="ws-progress-fill"
                    style={{ width: isCompleted ? '100%' : '0%' }}
                  />
                </div>
                <span className="ws-progress-label">{isCompleted ? 1 : 0} of 1</span>
              </div>
            </div>
            <button
              type="button"
              className="ws-scenario-toggle"
              onClick={() => setScenarioVisible((v) => !v)}
            >
              {scenarioVisible ? 'Hide scenario' : 'Show scenario'}
            </button>
          </div>
        </div>

        {scenarioVisible && (
          <div className="ws-scenario-banner">
            <span className="ws-scenario-banner-label">
              <FileTextIcon size={14} color="#7C3AED" /> SCENARIO
            </span>
            <p className="ws-scenario-banner-text">{activity.situation}</p>
            <span className="ws-scenario-banner-hint">
              {selectedArea ? selectedArea.label : 'Choose a highlighted area to begin.'}
            </span>
          </div>
        )}

        <div className="ws-workplace-canvas">
          <img src={workplaceImg} alt="Your workplace" className="ws-workplace-image" />
          {WORKPLACE_AREAS.map((area) => {
            const isRelevant = relevantAreaIds.has(area.id)
            const Icon = AREA_ICONS[area.icon]
            return (
              <button
                type="button"
                key={area.id}
                className={`ws-hotspot ${isRelevant ? 'ws-hotspot--active' : 'ws-hotspot--disabled'}`}
                style={{ left: `${area.left}%`, top: `${area.top}%` }}
                disabled={!isRelevant}
                onClick={() => setSelectedAreaId(area.id)}
                title={isRelevant ? undefined : 'Not relevant to your selected role'}
              >
                <span className="ws-hotspot-icon">
                  <Icon size={16} color={isRelevant ? '#7C3AED' : '#9CA3AF'} />
                </span>
                <span className="ws-hotspot-label">{area.label}</span>
              </button>
            )
          })}

          {selectedArea && (
            <div className={`ws-area-panel ${selectedArea.left > 50 ? 'ws-area-panel--left' : ''}`}>
              <span className="ws-prep-eyebrow ws-area-panel-eyebrow">
                {(() => { const Icon = AREA_ICONS[selectedArea.icon]; return <Icon size={14} color="#7C3AED" /> })()}
                {selectedArea.label.toUpperCase()}
              </span>
              {isPrimaryAreaSelected ? (
                <>
                  <h2 className="ws-area-panel-title">{activity.title}</h2>
                  <p className="ws-area-panel-text">{activity.situation}</p>
                  <div className="ws-area-panel-todo">
                    <span className="ws-prep-eyebrow">WHAT YOU NEED TO DO</span>
                    <p>{activity.task}</p>
                  </div>
                  <div className="ws-area-panel-actions">
                    {isCompleted ? (
                      <span className="ws-area-panel-done">
                        <span aria-hidden="true">&#10003;</span> Completed
                      </span>
                    ) : (
                      <button type="button" className="ws-intro-continue" onClick={handleStartTask}>
                        Start the task <span aria-hidden="true">→</span>
                      </button>
                    )}
                    <button type="button" className="ws-back-link" onClick={() => setSelectedAreaId(null)}>
                      Back to workplace
                    </button>
                  </div>
                </>
              ) : (
                // Only relevant (enabled) hotspots reach this popup at all,
                // so a non-primary selection is always one of the two
                // universal areas - a shared space, not a missing activity.
                <>
                  <h2 className="ws-area-panel-title">A shared space</h2>
                  <p className="ws-area-panel-text">
                    This is a shared space for the team - there&rsquo;s no specific activity here for this practice.
                  </p>
                  <div className="ws-area-panel-actions">
                    <button type="button" className="ws-back-link" onClick={() => setSelectedAreaId(null)}>
                      Back to workplace
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
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
            {HOW_IT_WORKS.map((item) => (
              <div key={item.number} className="ws-intro-step">
                <span className="ws-intro-step-number">{item.number}</span>
                <p>{item.text}</p>
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
