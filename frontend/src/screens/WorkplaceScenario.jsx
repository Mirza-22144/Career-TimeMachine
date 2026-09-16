import { useEffect, useState } from 'react'
import '../styles/WorkplaceScenario.css'
import TopNav from '../components/TopNav'
import workplaceImg from '../assets/workplace.png'
import { getSelectedRole, getPracticeState, setPracticeState } from '../practiceSession.js'
import { getPracticeScenario, getGenericAreaTask } from '../mockData/practiceScenario.js'
import { WORKPLACE_AREAS, getRelevantAreaIds } from '../mockData/workplaceAreas.js'
import {
  UserIcon, BarChartIcon, HeadsetIcon, FileTextIcon, LightbulbIcon, UsersIcon,
  FlaskIcon, CodeIcon, ShieldIcon, GlobeIcon, BellIcon, LayoutIcon,
} from '../components/icons'
import { api } from '../api.js'
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

const TOTAL_PRACTICE_STEPS = 3

// Reached after Your Direction's "Try a Workplace Scenario" (AC 4.1.2/4.1.3),
// or from the nav's Practice Scenarios link once a token is active. Walks
// through the intro (AC 4.2.1), the time/difficulty setup (AC 4.2.2), the
// prep screen (AC 4.2.3), then the interactive workplace (AC 4.3.1-4.3.4)
// for whichever role was carried over from Your Direction. The actual
// scored activity/feedback flow is still Iteration 2 backend/AI work.
export default function WorkplaceScenario() {
  const [loading, setLoading] = useState(true)
  // null | 'no-role' | 'intro-failed' | 'restore-failed'
  const [loadError, setLoadError] = useState(null)
  const [role, setRole] = useState(null)
  // 'intro' | 'setup' | 'prep' | 'workplace' | 'activity'
  const [step, setStep] = useState('intro')
  // Nothing pre-selected - Maya must explicitly choose both.
  const [duration, setDuration] = useState(null)
  const [difficulty, setDifficulty] = useState(null)
  const [attemptedContinue, setAttemptedContinue] = useState(false)
  // AC 4.2.3 - the prep screen's own data and loading/error state, kept
  // separate from the intro's loadError so a failure here doesn't wipe out
  // the duration/difficulty she already chose on the setup screen.
  const [prepLoading, setPrepLoading] = useState(false)
  const [prepError, setPrepError] = useState(false)
  const [scenario, setScenario] = useState(null)
  const [newSkillFocus, setNewSkillFocus] = useState(null)
  // AC 4.3.2 - the scenario banner can be hidden/shown, but stays loaded
  // and tied to the session either way.
  const [scenarioVisible, setScenarioVisible] = useState(true)
  // AC 4.3.3 - which hotspot's detail panel is open, if any.
  const [selectedAreaId, setSelectedAreaId] = useState(null)
  // AC 4.3.4 - how far into the practice she's got (fixed at step 1 of 3
  // for now - there's no real multi-activity backend yet to track this
  // against, so this reflects the same static example shown in the design).
  const [progress] = useState({ current: 1, total: TOTAL_PRACTICE_STEPS })

  const load = () => {
    const selected = getSelectedRole()
    if (!selected) {
      setLoadError('no-role')
      setLoading(false)
      return
    }
    setRole(selected)

    // AC 4.3.4: resume mid-practice (e.g. she left via the nav and came
    // back through "Practice Scenarios") instead of restarting the intro.
    const saved = getPracticeState()
    if (saved && saved.roleId === selected.id) {
      try {
        const restoredScenario = getPracticeScenario(selected.id, selected.label)
        setScenario(restoredScenario)
        setDuration(saved.duration)
        setDifficulty(saved.difficulty)
        setStep('workplace')
        setLoadError(null)
        setLoading(false)
      } catch {
        setLoadError('restore-failed')
        setLoading(false)
      }
      return
    }

    try {
      // Mocked "create a practice session" step (AC 4.1.3) - stands in for
      // a real backend session-creation call once BE/AI are ready. Also
      // covers AC 4.2.1's "introduction cannot be loaded" exception, since
      // this is the same load step that prepares the intro screen below.
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

  // AC 4.2.3: gathers what the prep screen shows - the (mocked) scenario
  // for her role, plus a real, current in-demand skill she hasn't already
  // recorded (GET /career-translation's new_horizons - the same "New
  // Horizons" data already used on the Skill Relevance Map).
  const loadPrep = async () => {
    setPrepLoading(true)
    setPrepError(false)
    try {
      const translation = await api.getCareerTranslation()
      setNewSkillFocus(translation.new_horizons?.[0]?.label || null)
      setScenario(getPracticeScenario(role.id, role.label))
      setPrepLoading(false)
    } catch {
      setPrepError(true)
      setPrepLoading(false)
    }
  }

  // AC 4.3.1/4.3.4: entering the workplace is what actually starts the
  // persisted practice session, so leaving and coming back restores it.
  const handleEnterWorkplace = () => {
    setPracticeState({ roleId: role.id, duration, difficulty })
    setStep('workplace')
  }

  const difficultyLabel = DIFFICULTIES.find((d) => d.value === difficulty)?.label
  const relevantAreaIds = role ? getRelevantAreaIds(role.id) : new Set()
  const startArea = scenario ? WORKPLACE_AREAS.find((a) => a.id === scenario.start_area_id) : null
  const selectedArea = selectedAreaId ? WORKPLACE_AREAS.find((a) => a.id === selectedAreaId) : null
  const selectedAreaTask = selectedArea
    ? (selectedArea.id === scenario?.start_area_id ? scenario.task_detail : getGenericAreaTask(selectedArea.label))
    : null

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

  if (step === 'activity') return (
    <>
      <TopNav />
      <div className="ws-page">
        <main className="ws-content">
          <span className="ws-eyebrow">WORKPLACE SCENARIO</span>
          <h1 className="ws-heading">Workplace activities are coming soon.</h1>
          <p className="ws-subheading">
            This is where you&rsquo;ll work through &ldquo;{scenario.title}&rdquo; ({difficultyLabel},{' '}
            {DURATIONS.find((d) => d.value === duration)?.caption}) for {role.label}.
          </p>
          <button type="button" className="ws-back-link" onClick={() => setStep('workplace')}>
            Back to Workplace
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
          <p className="ws-prep-subtitle">{role.label} - {scenario.workplace_area}</p>

          <div className="ws-prep-card">
            <span className="ws-prep-eyebrow">TODAY&rsquo;S FOCUS</span>
            <h2 className="ws-prep-title">{scenario.title}</h2>
            <hr className="ws-intro-divider" />

            <span className="ws-prep-eyebrow">YOU&rsquo;LL USE</span>
            <div className="ws-prep-pills">
              {scenario.skills_used.map((skill) => (
                <span key={skill} className="ws-prep-pill">{skill}</span>
              ))}
            </div>
            <hr className="ws-intro-divider" />

            <span className="ws-prep-eyebrow">YOU&rsquo;LL PRACTISE</span>
            <p className="ws-prep-task">{scenario.task}</p>
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
                    style={{ width: `${(progress.current / progress.total) * 100}%` }}
                  />
                </div>
                <span className="ws-progress-label">{progress.current} of {progress.total}</span>
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
            <p className="ws-scenario-banner-text">{scenario.situation}</p>
            <span className="ws-scenario-banner-hint">
              {selectedArea ? selectedArea.label : `Start with the ${startArea?.label}.`}
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
              <h2 className="ws-area-panel-title">{selectedAreaTask.character_name} has stopped by</h2>
              <p className="ws-area-panel-text">{selectedAreaTask.character_intro}</p>
              <div className="ws-area-panel-todo">
                <span className="ws-prep-eyebrow">WHAT YOU NEED TO DO</span>
                <p>{selectedAreaTask.what_to_do}</p>
              </div>
              <div className="ws-area-panel-actions">
                <button type="button" className="ws-intro-continue" onClick={() => setStep('activity')}>
                  Start the task <span aria-hidden="true">→</span>
                </button>
                <button type="button" className="ws-back-link" onClick={() => setSelectedAreaId(null)}>
                  Back to workplace
                </button>
              </div>
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
