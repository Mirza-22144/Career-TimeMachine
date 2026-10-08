import { useEffect, useState } from 'react'
import '../styles/WorkplaceScenario.css'
import '../styles/PracticeActivity.css'
import TopNav from '../components/TopNav'
import ChoiceActivity from '../components/practice/ChoiceActivity'
import DragDropActivity from '../components/practice/DragDropActivity'
import PracticeFeedback, { ActivitySkeleton } from '../components/practice/PracticeFeedback'
import workplaceImg from '../assets/workplace.png'
import { WORKPLACE_AREAS } from '../mockData/workplaceAreas.js'
import { loadPracticeSession } from '../mockData/practiceSession.js'
import {
  UserIcon, BarChartIcon, HeadsetIcon, FileTextIcon, LightbulbIcon, UsersIcon,
  FlaskIcon, CodeIcon, ShieldIcon, GlobeIcon, BellIcon, LayoutIcon, CheckIcon, ArrowRightIcon,
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
  { number: 1, text: 'Explore your workplace. One area at a time will need you.' },
  { number: 2, text: 'Complete a realistic workplace activity when you get there.' },
  { number: 3, text: 'Get feedback on what you did well and what you could explore further.' },
]

// AC 4.1.4: Easy, Standard and Complex, with no time estimate.
const DIFFICULTIES = [
  { value: 'guided', label: 'Easy', caption: 'More prompts along the way' },
  { value: 'standard', label: 'Standard', caption: 'Work through it as you would at work' },
  { value: 'challenge', label: 'Complex', caption: 'Less context, more to weigh up' },
]

const areaById = (id) => WORKPLACE_AREAS.find((area) => area.id === id)

// Workplace practice: intro -> difficulty -> preparation -> the workplace
// floor, where activities unlock one at a time (she never sees what is
// coming next) -> each activity and its feedback -> the soft stop.
//
// The role and practice focus are real (GET /practice-role, GET /roadmap).
// The activities themselves are frontend-only mock content for now - see
// mockData/practiceSession.js - so nothing she does here is saved yet.
export default function WorkplaceScenario() {
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null) // null | 'no-role' | 'intro-failed'
  const [role, setRole] = useState(null)
  // 'intro' | 'setup' | 'prep' | 'workplace' | 'activity' | 'feedback' | 'stop'
  const [step, setStep] = useState('intro')
  const [difficulty, setDifficulty] = useState(null)
  const [prepLoading, setPrepLoading] = useState(false)
  const [prepError, setPrepError] = useState(false)
  const [focusSkill, setFocusSkill] = useState(null)
  const [skillsUsed, setSkillsUsed] = useState([])
  const [activities, setActivities] = useState([])
  // Index of the one activity currently unlocked; everything before it is done.
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState({}) // activity id -> her answer
  const [isPreparingActivity, setIsPreparingActivity] = useState(false)
  const [scenarioVisible, setScenarioVisible] = useState(true)
  const [isPanelOpen, setIsPanelOpen] = useState(false)
  const [toast, setToast] = useState('')

  const load = async () => {
    try {
      const practiceRole = await api.getPracticeRole()
      if (!practiceRole.role_id) {
        setLoadError('no-role')
        setLoading(false)
        return
      }
      setRole({ id: practiceRole.role_id, label: practiceRole.role_label })
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

  useEffect(() => {
    if (!toast) return undefined
    const timer = setTimeout(() => setToast(''), 5000)
    return () => clearTimeout(timer)
  }, [toast])

  const retryLoad = () => {
    setLoading(true)
    load()
  }

  // Preparation page data: her practice focus and the skills she'll use,
  // from the roadmap of the role she chose, plus the session's activities.
  const loadPrep = async () => {
    setPrepLoading(true)
    setPrepError(false)
    try {
      const [roadmap, practice] = await Promise.all([api.getRoadmap(), loadPracticeSession()])
      const practised = [roadmap.previous_role, ...roadmap.suggested_roles].find(
        (r) => r && r.role_id === roadmap.selected_role_id,
      )
      setFocusSkill(practised?.skills_could_explore.find((s) => s.status === 'next')?.label || null)
      setSkillsUsed((practised?.skills_bring_back || []).map((s) => s.label))
      setActivities(practice.activities)
      setCurrentIndex(0)
      setAnswers({})
      setPrepLoading(false)
    } catch {
      setPrepError(true)
      setPrepLoading(false)
    }
  }

  const handleSetupContinue = () => {
    setStep('prep')
    loadPrep()
  }

  // Shows the "Setting up this situation…" layout for as long as the
  // activity takes to be ready. Instant with today's local content; this
  // is where a slow backend or live-generated activity will be waited on.
  const openActivity = async () => {
    setIsPanelOpen(false)
    setIsPreparingActivity(true)
    setStep('activity')
    try {
      await loadPracticeSession()
    } finally {
      setIsPreparingActivity(false)
    }
  }

  const handleSubmit = (answer) => {
    setAnswers((prev) => ({ ...prev, [activity.id]: answer }))
    setStep('feedback')
  }

  // After feedback: the next activity unlocks on the floor, or - after the
  // last one - the soft stop.
  const handleFeedbackContinue = () => {
    const nextIndex = currentIndex + 1
    if (nextIndex >= activities.length) {
      setCurrentIndex(nextIndex)
      setStep('stop')
      return
    }
    setCurrentIndex(nextIndex)
    setToast(`Something new has come in at the ${areaById(activities[nextIndex].areaId).label}.`)
    setStep('workplace')
  }

  const handleKeepGoing = () => {
    setStep('prep')
    loadPrep()
  }

  const activity = activities[currentIndex] || null
  const area = activity ? areaById(activity.areaId) : null
  const completedCount = Math.min(currentIndex, activities.length)
  const difficultyLabel = DIFFICULTIES.find((d) => d.value === difficulty)?.label

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
            {loadError === 'no-role' && 'Choose a role to practise on your roadmap first.'}
            {loadError === 'intro-failed' && "We couldn't start your workplace practice. Please try again."}
          </p>
          {loadError === 'intro-failed' && <button type="button" onClick={retryLoad}>Try Again</button>}
          <button type="button" className="ws-load-error-link" onClick={() => navigate('/your-roadmap')}>
            {loadError === 'no-role' ? 'Open Your Roadmap' : 'Back to Your Roadmap'}
          </button>
        </div>
      </div>
    </>
  )

  if ((step === 'activity' || step === 'feedback') && activity) return (
    <>
      <TopNav />
      <div className="pa-page">
        <div className="pa-topbar">
          <button type="button" className="pa-back" onClick={() => setStep('workplace')}>
            <span aria-hidden="true">&larr;</span> Back to workplace
          </button>
          <span className="pa-breadcrumb">
            {role.label} · {area.label}
            <span className="pa-count">{currentIndex + 1} of {activities.length}</span>
          </span>
        </div>
        {step === 'activity' && isPreparingActivity && <ActivitySkeleton areaLabel={area.label} />}
        {step === 'activity' && !isPreparingActivity && activity.type === 'drag_and_drop' && (
          <DragDropActivity key={activity.id} activity={activity} areaLabel={area.label} onSubmit={handleSubmit} />
        )}
        {step === 'activity' && !isPreparingActivity && activity.type !== 'drag_and_drop' && (
          <ChoiceActivity key={activity.id} activity={activity} areaLabel={area.label} onSubmit={handleSubmit} />
        )}
        {step === 'feedback' && (
          <PracticeFeedback
            activity={activity}
            answer={answers[activity.id]}
            areaLabel={area.label}
            isLast={currentIndex === activities.length - 1}
            onContinue={handleFeedbackContinue}
          />
        )}
      </div>
    </>
  )

  // AC 4.5.4: the soft stop.
  if (step === 'stop') return (
    <>
      <TopNav />
      <div className="pa-page">
        <main className="pa-body pa-body--stop">
          <span className="pa-eyebrow">SESSION COMPLETE</span>
          <h1 className="pa-stop-heading">That&rsquo;s today&rsquo;s practice.</h1>
          <p className="pa-stop-subheading">Come back anytime, or keep going if you have time.</p>
          <div className="pa-card pa-stop-list">
            {activities.map((item) => (
              <div className="pa-stop-row" key={item.id}>
                <span className="pa-stop-check"><CheckIcon size={13} color="#3730A3" /></span>
                {item.title}
                <span className="pa-stop-area">{areaById(item.areaId).label}</span>
              </div>
            ))}
          </div>
        </main>
        <div className="pa-footer">
          <span className="pa-footer-note">You&rsquo;ve finished all {activities.length} activities in this session.</span>
          <div className="pa-footer-actions">
            <button type="button" className="pa-btn-outline" onClick={handleKeepGoing}>Keep Going</button>
            <button type="button" className="pa-btn-primary" onClick={() => navigate('/dashboard')}>
              Finish Practice <ArrowRightIcon size={16} />
            </button>
          </div>
        </div>
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
            Choose how challenging you&rsquo;d like this practice to be.
          </p>

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

          <button type="button" className="ws-intro-continue" disabled={!difficulty} onClick={handleSetupContinue}>
            Continue <span aria-hidden="true">→</span>
          </button>
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
          <p>We couldn&rsquo;t start your workplace practice. Please try again.</p>
          <button type="button" onClick={loadPrep}>Try Again</button>
        </div>
      </div>
    </>
  )

  // AC 4.1.4: practice focus, skills she'll use and difficulty - no time
  // estimate, and nothing about the situations she will meet.
  if (step === 'prep') return (
    <>
      <TopNav />
      <div className="ws-page">
        <main className="ws-prep-content">
          <h1 className="ws-intro-heading">Your practice</h1>
          <p className="ws-prep-subtitle">{role.label}</p>

          <div className="ws-prep-layout">
            <div className="ws-prep-main">
              <span className="ws-prep-eyebrow">YOUR PRACTICE FOCUS</span>
              <h2 className="ws-prep-title">{focusSkill || `Working as a ${role.label}`}</h2>
              <p className="ws-prep-task">
                A few short workplace situations, one at a time. You&rsquo;ll see what each one involves when you
                get there.
              </p>
            </div>
            <aside className="ws-prep-side">
              <div>
                <span className="ws-prep-eyebrow">DIFFICULTY</span>
                <strong className="ws-prep-footer-value">{difficultyLabel}</strong>
              </div>
              {skillsUsed.length > 0 && (
                <div>
                  <span className="ws-prep-eyebrow">YOU&rsquo;LL USE</span>
                  <div className="ws-prep-pills">
                    {skillsUsed.map((skill) => (
                      <span key={skill} className="ws-prep-pill">{skill}</span>
                    ))}
                  </div>
                </div>
              )}
            </aside>
          </div>

          <button type="button" className="ws-intro-continue" onClick={() => setStep('workplace')}>
            Enter Workplace <span aria-hidden="true">→</span>
          </button>
        </main>
      </div>
    </>
  )

  if (step === 'workplace' && activity) {
    const doneAreaIds = new Set(activities.slice(0, currentIndex).map((item) => item.areaId))
    const PanelIcon = AREA_ICONS[area.icon]
    return (
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
                      style={{ width: `${(completedCount / activities.length) * 100}%` }}
                    />
                  </div>
                  <span className="ws-progress-label">{completedCount} of {activities.length}</span>
                </div>
              </div>
              <button type="button" className="ws-scenario-toggle" onClick={() => setScenarioVisible((v) => !v)}>
                {scenarioVisible ? 'Hide scenario' : 'Show scenario'}
              </button>
            </div>
          </div>

          {scenarioVisible && (
            <div className="ws-scenario-banner">
              <span className="ws-scenario-banner-label">
                <FileTextIcon size={14} color="#7C3AED" /> TODAY
              </span>
              <p className="ws-scenario-banner-text">{activity.announcement}</p>
              <span className="ws-scenario-banner-hint">You will see what it involves when you get there.</span>
            </div>
          )}

          <div className={`ws-workplace-canvas ${isPanelOpen ? 'pa-canvas--dimmed' : ''}`}>
            <img src={workplaceImg} alt="Your workplace" className="ws-workplace-image" />
            {WORKPLACE_AREAS.map((item) => {
              const isCurrent = item.id === area.id
              const isDone = doneAreaIds.has(item.id)
              const Icon = AREA_ICONS[item.icon]
              return (
                <button
                  type="button"
                  key={item.id}
                  className={`ws-hotspot ${isCurrent ? 'ws-hotspot--active pa-hotspot--current' : ''} ${isDone ? 'pa-hotspot--done' : ''} ${!isCurrent && !isDone ? 'ws-hotspot--disabled' : ''}`}
                  style={{ left: `${item.left}%`, top: `${item.top}%` }}
                  disabled={!isCurrent}
                  aria-label={isDone ? `${item.label}, completed` : item.label}
                  onClick={() => setIsPanelOpen(true)}
                >
                  <span className="ws-hotspot-icon">
                    {isDone ? <CheckIcon size={14} /> : <Icon size={16} color={isCurrent ? '#7C3AED' : '#9CA3AF'} />}
                  </span>
                  <span className="ws-hotspot-label">{item.label}</span>
                </button>
              )
            })}

            {isPanelOpen && (
              <div className={`ws-area-panel ${area.left > 50 ? 'ws-area-panel--left' : ''}`}>
                <span className="ws-prep-eyebrow ws-area-panel-eyebrow">
                  <PanelIcon size={14} color="#7C3AED" />
                  {area.label.toUpperCase()}
                </span>
                <h2 className="ws-area-panel-title">{activity.panel.title}</h2>
                <p className="ws-area-panel-text">{activity.panel.text}</p>
                <div className="ws-area-panel-actions">
                  <button type="button" className="ws-intro-continue" onClick={openActivity}>
                    {activity.panel.cta} <span aria-hidden="true">→</span>
                  </button>
                  <button type="button" className="ws-back-link" onClick={() => setIsPanelOpen(false)}>
                    Not now
                  </button>
                </div>
              </div>
            )}

            {toast && !isPanelOpen && <div className="pa-toast" role="status">{toast}</div>}
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      <TopNav />
      <div className="ws-page">
        <main className="ws-intro-content">
          <h1 className="ws-intro-heading">Welcome to your practice area</h1>
          <p className="ws-intro-subheading">
            You&rsquo;ll work through a few realistic workplace situations as a {role.label}, with a hint whenever
            you want one.
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
