import { useEffect, useRef, useState } from 'react'
import '../styles/WorkplaceScenario.css'
import '../styles/PracticeActivity.css'
import TopNav from '../components/TopNav'
import LoadingPopup from '../components/LoadingPopup'
import ChoiceActivity from '../components/practice/ChoiceActivity'
import DragDropActivity from '../components/practice/DragDropActivity'
import PracticeFeedback, { ActivitySkeleton } from '../components/practice/PracticeFeedback'
import workplaceImg from '../assets/workplace.webp'
import introImg from '../assets/practice-intro.webp'
import { WORKPLACE_AREAS, getPrimaryAreaId } from '../mockData/workplaceAreas.js'
import { loadMockActivities } from '../mockData/practiceSession.js'
import {
  UserIcon, BarChartIcon, HeadsetIcon, FileTextIcon, LightbulbIcon, UsersIcon,
  FlaskIcon, CodeIcon, ShieldIcon, GlobeIcon, BellIcon, LayoutIcon, CheckIcon, ArrowRightIcon,
} from '../components/icons'
import { api } from '../api.js'
import { navigate } from '../navigate.js'
import { addCompleted, clearPending, getPending, hasCompleted, setPending } from '../practiceHistory.js'
import { toChoiceActivity } from '../practiceAdapters.js'

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

// AC 4.1.4: Easy, Standard and Complex, with no time estimate.
const DIFFICULTIES = [
  { value: 'guided', label: 'Easy', caption: 'More prompts along the way' },
  { value: 'standard', label: 'Standard', caption: 'Work through it as you would at work' },
  { value: 'challenge', label: 'Complex', caption: 'Less context, more to weigh up' },
]

const areaById = (id) => WORKPLACE_AREAS.find((area) => area.id === id)

const MCQ = 'multiple_choice'

// AC 4.3.5 exception.
const MAY_REPEAT = 'We couldn’t check your earlier activities, so some may repeat.'

// What the floor says about the multiple-choice activity before she opens
// it. It never describes the situations themselves.
const mcqFloor = (roleLabel, areaLabel, completed) => ({
  announcement: `Something needs you in the ${areaLabel}.`,
  panel: {
    title: 'A few situations need your judgement',
    // No count here: a question about her own skill can still be on its way.
    text: `Situations a ${roleLabel} meets at work, one at a time. You will see each one when you get there.`,
    cta: completed > 0 ? 'Carry on' : 'See the first one',
  },
})

function SettingUp({ text }) {
  return (
    <>
      <TopNav />
      <div className="pa-page">
        <main className="pa-body pa-body--stop" aria-busy="true" />
        <LoadingPopup text={text} />
      </div>
    </>
  )
}

// Workplace practice: intro -> difficulty -> preparation -> the workplace
// floor -> one activity -> the soft stop.
//
// There are three kinds of activity: Multiple Choice, Code Review and Drag
// and Drop. Only one is unlocked at a time, picked at random from the ones
// she has not done for this role and level, so she never sees what is
// coming. An activity has to be finished before another one opens. When it
// is, the soft stop appears and the next one is unlocked: Keep Going opens
// it now, Finish Practice leaves it waiting for her next visit.
//
// Multiple Choice is real: POST /practice-sessions builds an activity of
// four questions (plus a live one about a skill she typed in herself), the
// backend hands them over one at a time and stores her answers and
// feedback, so leaving part-way and coming back resumes at the same
// question. Code Review and Drag and Drop are still mock content - see
// mockData/practiceSession.js.
export default function WorkplaceScenario() {
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null) // null | 'no-role' | 'intro-failed'
  const [role, setRole] = useState(null)
  // 'intro' | 'resume' | 'ready' | 'setup' | 'prep' | 'workplace' | 'activity' | 'feedback' | 'stop' | 'exhausted'
  const [step, setStep] = useState('intro')
  const [difficulty, setDifficulty] = useState(null)
  const [isStarting, setIsStarting] = useState(false)
  const [startError, setStartError] = useState(false)
  const [focusSkill, setFocusSkill] = useState(null)
  const [skillsUsed, setSkillsUsed] = useState([])
  const [mockActivities, setMockActivities] = useState([])
  // The one kind of activity currently unlocked.
  const [kind, setKind] = useState(null)
  // The multiple-choice activity in progress: { id, total, completed }.
  const [session, setSession] = useState(null)
  // Its current question, as the API returns it.
  const [question, setQuestion] = useState(null)
  const [questionError, setQuestionError] = useState(false)
  // Titles finished in the current activity, for the soft stop.
  const [finished, setFinished] = useState([])
  // What the feedback step shows: { activity, answer } or { activity, feedback, hasNext }.
  const [result, setResult] = useState(null)
  // The activity unlocked after this one: 'checking' while it is being
  // worked out, null when nothing new is left, 'retry' if that check failed.
  const [nextKind, setNextKind] = useState(null)
  // New multiple-choice questions left per difficulty (GET /practice-sessions/remaining).
  const [remaining, setRemaining] = useState(null)
  // True when her earlier activities could not be checked for the activity
  // now open (AC 4.3.5 exception): she continues, and is told some may repeat.
  const [mayRepeat, setMayRepeat] = useState(false)
  const unchecked = useRef(false)
  const sessionFocus = useRef(null)
  // Requested as soon as the page opens, so they are usually ready by the
  // time she has chosen a level. Each is used once, then fetched fresh.
  const early = useRef({ roadmap: null, remaining: null })
  const fetchEarly = (key, fetcher) => {
    const request = fetcher()
    request.catch(() => {}) // a failure is handled where it is awaited
    early.current[key] = request
  }
  const takeEarly = (key, fetcher) => {
    const request = early.current[key] || fetcher()
    early.current[key] = null
    return request
  }
  // Areas of the floor finished in this visit.
  const [doneAreaIds, setDoneAreaIds] = useState([])
  const [isPreparingActivity, setIsPreparingActivity] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [scenarioVisible, setScenarioVisible] = useState(true)
  const [isPanelOpen, setIsPanelOpen] = useState(false)
  const [toast, setToast] = useState('')

  const applySession = (apiSession) => {
    const { progress } = apiSession
    setSession({ id: apiSession.session_id, total: progress.total_activities, completed: progress.completed_activities })
    setQuestion(apiSession.scenarios.find((item) => item.scenario_id === progress.current_scenario_id) || null)
    setFinished(apiSession.scenarios.filter((item) => item.status === 'completed').map((item) => item.title))
  }

  // Only the latest call may change the screen. React runs the first load
  // twice in development, and a slow earlier call must not undo what she
  // has done since.
  const loadTurn = useRef(0)

  const load = async () => {
    const turn = ++loadTurn.current
    const isStale = () => turn !== loadTurn.current
    try {
      const practiceRole = await api.getPracticeRole()
      if (isStale()) return
      if (!practiceRole.role_id) {
        setLoadError('no-role')
        setLoading(false)
        return
      }
      setRole({ id: practiceRole.role_id, label: practiceRole.role_label })
      fetchEarly('roadmap', api.getRoadmap)
      fetchEarly('remaining', api.getRemainingQuestions)
      const mocks = await loadMockActivities()
      if (isStale()) return
      setMockActivities(mocks)

      // An activity she left part-way through has to be finished first.
      let current = null
      try {
        current = await api.getCurrentPracticeSession()
      } catch (err) {
        if (err.code !== 'PRACTICE_SESSION_NOT_FOUND') throw err
      }
      if (isStale()) return
      if (current && current.progress.current_scenario_id) {
        setRole({ id: current.role.id, label: current.role.label })
        setDifficulty(current.difficulty)
        setKind(MCQ)
        applySession(current)
        setStep('resume')
      } else {
        // Every question was answered but the tab closed before it was
        // marked finished.
        if (current) await api.completePracticeSession(current.session_id).catch(() => {})
        if (isStale()) return
        // The activity unlocked at her last soft stop is still waiting.
        const pending = getPending(practiceRole.role_id)
        if (pending) {
          setDifficulty(pending.difficulty)
          setNextKind(pending.kind)
          setStep('ready')
        }
      }
      setLoadError(null)
      setLoading(false)
    } catch {
      if (isStale()) return
      setLoadError('intro-failed')
      setLoading(false)
    }
  }

  useEffect(() => {
    function run() {
      load()
    }
    run()
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  const areaIdFor = (activityKind) =>
    activityKind === MCQ ? getPrimaryAreaId(role.id) : mockActivities.find((item) => item.type === activityKind)?.areaId

  const mockLeft = (level) => mockActivities.filter((item) => !hasCompleted(role.id, level, item.id))
  // Unknown counts (the check failed) are treated as "there may be more".
  const levelHasWork = (level, counts) => !counts || counts[level] > 0 || mockLeft(level).length > 0

  // Picks, at random, a kind of activity she has not done for this role and
  // level - or null when nothing new is left (AC 4.3.5).
  const pickNext = async (level, { withoutMcq = false } = {}) => {
    let counts = null
    try {
      counts = await takeEarly('remaining', api.getRemainingQuestions)
    } catch {
      // AC 4.3.5 exception: she still practises; Multiple Choice is assumed
      // to have something left and the backend has the final say.
      unchecked.current = true
    }
    setRemaining(counts)
    const mcqLeft = !withoutMcq && (!counts || counts[level] > 0)
    const kinds = [...(mcqLeft ? [MCQ] : []), ...mockLeft(level).map((item) => item.type)]
    return kinds.length > 0 ? kinds[Math.floor(Math.random() * kinds.length)] : null
  }

  // Opens the picked activity. Multiple Choice is prepared by the backend
  // (a few seconds when a live question is being written). Returns false if
  // it turned out there was nothing new after all.
  const enter = async (activityKind, level) => {
    if (activityKind === MCQ) {
      try {
        const started = await api.startPracticeSession('standard', level)
        if (started.history_checked === false) unchecked.current = true
        sessionFocus.current = started.focus_skill || null
        applySession(started)
      } catch (err) {
        if (err.code !== 'NO_NEW_ACTIVITIES') throw err
        return false
      }
      // From here the backend holds her place.
      clearPending()
    } else {
      setSession(null)
      setQuestion(null)
      setFinished([])
      setPending({ roleId: role.id, difficulty: level, kind: activityKind })
    }
    setKind(activityKind)
    return true
  }

  const pickAndEnter = async (level, preferred) => {
    unchecked.current = false
    sessionFocus.current = null
    const opened = await (async () => {
      // A waiting activity she has since completed elsewhere is not reopened.
      const stillNew = preferred === MCQ || mockLeft(level).some((item) => item.type === preferred)
      if (preferred && stillNew && (await enter(preferred, level))) return preferred
      let picked = await pickNext(level, { withoutMcq: preferred === MCQ })
      if (picked === MCQ && !(await enter(MCQ, level))) picked = await pickNext(level, { withoutMcq: true })
      if (picked === MCQ) return MCQ
      if (picked && (await enter(picked, level))) return picked
      clearPending()
      return null
    })()
    setMayRepeat(Boolean(opened) && unchecked.current)
    return opened
  }

  // Preparation page: her practice focus and the skills she'll use come
  // from the roadmap of the role she chose. Both run together behind the
  // "Setting up" screen.
  const startPractice = async () => {
    setIsStarting(true)
    setStartError(false)
    try {
      const [roadmap, unlocked] = await Promise.all([
        takeEarly('roadmap', api.getRoadmap),
        pickAndEnter(difficulty, null),
      ])
      if (!unlocked) {
        setStep('exhausted')
        return
      }
      const practised = [roadmap.previous_role, ...roadmap.suggested_roles].find(
        (r) => r && r.role_id === roadmap.selected_role_id,
      )
      // The activity's own focus when it has one (a skill from her roadmap
      // its questions use), otherwise the next skill on her roadmap.
      setFocusSkill(
        sessionFocus.current || practised?.skills_could_explore.find((item) => item.status === 'next')?.label || null,
      )
      setSkillsUsed((practised?.skills_bring_back || []).map((item) => item.label))
      setStep('prep')
    } catch (err) {
      // Another tab started an activity: it has to be finished first.
      if (err.code === 'ACTIVITY_IN_PROGRESS') retryLoad()
      else setStartError(true)
    } finally {
      setIsStarting(false)
    }
  }

  // AC 4.5.4: Keep Going (or coming back another day) opens the activity
  // that was unlocked at the soft stop.
  const handleKeepGoing = async () => {
    setIsStarting(true)
    setStartError(false)
    try {
      const preferred = nextKind && nextKind !== 'checking' && nextKind !== 'retry' ? nextKind : null
      const unlocked = await pickAndEnter(difficulty, preferred)
      if (!unlocked) {
        setStep('exhausted')
        return
      }
      setToast(unchecked.current ? MAY_REPEAT : `Something new has come in at the ${areaById(areaIdFor(unlocked)).label}.`)
      setStep('workplace')
    } catch (err) {
      if (err.code === 'ACTIVITY_IN_PROGRESS') retryLoad()
      else setStartError(true)
    } finally {
      setIsStarting(false)
    }
  }

  // The activity is finished: show the soft stop and unlock the next one,
  // which waits for her if she stops here.
  const finishActivity = async () => {
    setDoneAreaIds((ids) => [...ids, areaIdFor(kind)])
    setNextKind('checking')
    setStep('stop')
    try {
      const picked = await pickNext(difficulty)
      // Her practice focus may have moved on with what she just finished.
      fetchEarly('roadmap', api.getRoadmap)
      setNextKind(picked)
      if (picked) setPending({ roleId: role.id, difficulty, kind: picked })
      else clearPending()
    } catch {
      setNextKind('retry')
    }
  }

  const openActivity = () => {
    setIsPanelOpen(false)
    setSubmitError('')
    setStep('activity')
  }

  // The backend only hands over a question once the one before it is
  // answered, so the next one is fetched here.
  const loadNextQuestion = async () => {
    setQuestionError(false)
    setIsPreparingActivity(true)
    setStep('activity')
    try {
      applySession(await api.getPracticeSession(session.id))
    } catch {
      setQuestionError(true)
    } finally {
      setIsPreparingActivity(false)
    }
  }

  const handleSubmit = async (answer) => {
    if (kind !== MCQ) {
      addCompleted({
        activityId: mock.id,
        title: mock.title,
        type: mock.type,
        answer,
        roleId: role.id,
        roleLabel: role.label,
        difficulty,
      })
      clearPending()
      setFinished([mock.title])
      setResult({ activity: mock, answer })
      setStep('feedback')
      return
    }
    setIsSubmitting(true)
    setSubmitError('')
    try {
      const saved = await api.submitScenarioResponse(session.id, question.scenario_id, { selected_option_id: answer })
      const hasNext = Boolean(saved.progress.current_scenario_id)
      // Finishing the activity frees her to start another one later. If
      // this call is lost, the next visit finishes it instead.
      if (!hasNext) api.completePracticeSession(session.id).catch(() => {})
      // The total can grow by one: the question about her own skill is
      // written after the activity starts and joins it when ready.
      setSession((value) => ({
        ...value,
        completed: saved.progress.completed_activities,
        total: saved.progress.total_activities,
      }))
      setFinished((titles) => [...titles, question.title])
      setResult({ activity: toChoiceActivity(question), feedback: saved.scenario.feedback, hasNext })
      setStep('feedback')
    } catch {
      setSubmitError("We couldn't save your answer. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  // After feedback: the next question in the activity, or the soft stop.
  const handleFeedbackContinue = () => {
    if (result.hasNext) {
      loadNextQuestion()
      return
    }
    finishActivity()
  }

  const mock = kind && kind !== MCQ ? mockActivities.find((item) => item.type === kind) : null
  const area = kind ? areaById(areaIdFor(kind)) : null
  const total = kind === MCQ ? session?.total || 0 : 1
  const completedCount = kind === MCQ ? session?.completed || 0 : 0
  const activity = kind === MCQ ? (question ? toChoiceActivity(question) : null) : mock
  const floor = kind === MCQ && area ? mcqFloor(role.label, area.label, completedCount) : mock
  const difficultyLabel = DIFFICULTIES.find((d) => d.value === difficulty)?.label

  if (loading) return (
    <>
      <TopNav />
      <div className="ws-page"><LoadingPopup text="Opening your practice…" /></div>
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

  if (isStarting) return <SettingUp text="Setting up your practice…" />

  if (startError) return (
    <>
      <TopNav />
      <div className="ws-page">
        <div className="ws-load-error">
          <p>We couldn&rsquo;t start your workplace practice. Please try again.</p>
          <button type="button" onClick={step === 'setup' ? startPractice : handleKeepGoing}>Try Again</button>
        </div>
      </div>
    </>
  )

  // She left an activity part-way through: it has to be finished before
  // anything else opens.
  if (step === 'resume') return (
    <>
      <TopNav />
      <div className="pa-page">
        <main className="pa-body pa-body--stop">
          <span className="pa-eyebrow">{role.label.toUpperCase()} · {difficultyLabel?.toUpperCase()}</span>
          <h1 className="pa-stop-heading pa-stop-heading--small">You have an activity to finish.</h1>
          <p className="pa-stop-subheading">
            You left at situation {completedCount + 1} of {total}. Finish this activity before starting something new.
          </p>
        </main>
        <div className="pa-footer">
          <span className="pa-footer-note">Your earlier answers are saved.</span>
          <button type="button" className="pa-btn-primary" onClick={() => setStep('workplace')}>
            Continue Activity <ArrowRightIcon size={16} />
          </button>
        </div>
      </div>
    </>
  )

  // The activity unlocked at her last soft stop, waiting since then.
  if (step === 'ready') return (
    <>
      <TopNav />
      <div className="pa-page">
        <main className="pa-body pa-body--stop">
          <span className="pa-eyebrow">{role.label.toUpperCase()} · {difficultyLabel?.toUpperCase()}</span>
          <h1 className="pa-stop-heading pa-stop-heading--small">Your next activity is ready.</h1>
          <p className="pa-stop-subheading">It was unlocked when you finished last time. You will see what it involves when you get there.</p>
        </main>
        <div className="pa-footer">
          <span className="pa-footer-note">Nothing here is graded.</span>
          <button type="button" className="pa-btn-primary" onClick={handleKeepGoing}>
            Enter Workplace <ArrowRightIcon size={16} />
          </button>
        </div>
      </div>
    </>
  )

  if (step === 'activity' || step === 'feedback') return (
    <>
      <TopNav />
      <div className="pa-page">
        <div className="pa-topbar">
          {step === 'activity' ? (
            <button type="button" className="pa-back" onClick={() => setStep('workplace')}>
              <span aria-hidden="true">&larr;</span> Back to workplace
            </button>
          ) : <span />}
          <span className="pa-breadcrumb">
            {role.label} · {area.label}
            <span className="pa-count">
              {step === 'feedback' ? Math.max(completedCount, 1) : Math.min(completedCount + 1, total)} of {total}
            </span>
          </span>
        </div>
        {step === 'activity' && isPreparingActivity && <ActivitySkeleton areaLabel={area.label} />}
        {step === 'activity' && !isPreparingActivity && questionError && (
          <main className="pa-body">
            <p className="pa-loading">We couldn&rsquo;t open the next situation. Please try again.</p>
            <button type="button" className="pa-btn-outline" onClick={loadNextQuestion}>Try Again</button>
          </main>
        )}
        {step === 'activity' && !isPreparingActivity && !questionError && activity?.type === 'drag_and_drop' && (
          <DragDropActivity key={activity.id} activity={activity} areaLabel={area.label} onSubmit={handleSubmit} />
        )}
        {step === 'activity' && !isPreparingActivity && !questionError && activity && activity.type !== 'drag_and_drop' && (
          <ChoiceActivity
            key={activity.id}
            activity={activity}
            areaLabel={area.label}
            isSubmitting={isSubmitting}
            submitError={submitError}
            onSubmit={handleSubmit}
          />
        )}
        {step === 'feedback' && (
          <PracticeFeedback
            activity={result.activity}
            answer={result.answer}
            feedback={result.feedback}
            areaLabel={area.label}
            continueLabel={result.hasNext ? 'Next Situation' : 'Continue'}
            onContinue={handleFeedbackContinue}
          />
        )}
      </div>
    </>
  )

  const runOutChoices = (
    <div className="pa-choice-row">
      {DIFFICULTIES.some((d) => d.value !== difficulty && levelHasWork(d.value, remaining)) && (
        <button type="button" className="pa-btn-primary" onClick={() => { setDifficulty(null); setStep('setup') }}>
          Try Another Difficulty
        </button>
      )}
      <button type="button" className="pa-btn-outline" onClick={() => navigate('/your-roadmap')}>
        Explore Another Role
      </button>
      <button type="button" className="pa-btn-outline" onClick={() => navigate('/analyse-job-description')}>
        Analyse a Job Description
      </button>
    </div>
  )

  // AC 4.5.4: the soft stop, after each activity. When nothing new is left
  // the "activities run out" choices take the place of Keep Going.
  if (step === 'stop') return (
    <>
      <TopNav />
      <div className="pa-page">
        <main className="pa-body pa-body--stop">
          <span className="pa-eyebrow">ACTIVITY COMPLETE</span>
          <h1 className="pa-stop-heading">That&rsquo;s today&rsquo;s practice.</h1>
          <p className="pa-stop-subheading">
            {nextKind === null
              ? 'Come back anytime.'
              : 'Come back anytime, or keep going if you have time.'}
          </p>
          <div className="pa-card pa-stop-list">
            {finished.map((title, index) => (
              <div className="pa-stop-row" key={`${title}-${index}`}>
                <span className="pa-stop-check"><CheckIcon size={13} color="#3730A3" /></span>
                {title}
                <span className="pa-stop-area">{area.label}</span>
              </div>
            ))}
          </div>
          {nextKind === null && (
            <div className="pa-run-out">
              <p className="pa-run-out-text">You&rsquo;ve completed all the activities for this role at this level.</p>
              {runOutChoices}
            </div>
          )}
        </main>
        <div className="pa-footer">
          <span className="pa-footer-note">
            {nextKind && nextKind !== 'checking' && nextKind !== 'retry'
              ? 'Your next activity is unlocked. It will wait for you if you stop here.'
              : 'Everything you did is saved to your dashboard.'}
          </span>
          <div className="pa-footer-actions">
            {nextKind !== null && (
              <button type="button" className="pa-btn-outline" disabled={nextKind === 'checking'} onClick={handleKeepGoing}>
                Keep Going
              </button>
            )}
            <button type="button" className="pa-btn-primary" onClick={() => navigate('/dashboard')}>
              Finish Practice <ArrowRightIcon size={16} />
            </button>
          </div>
        </div>
      </div>
    </>
  )

  // AC 4.3.5 exception: every activity for this role and level is done.
  if (step === 'exhausted') return (
    <>
      <TopNav />
      <div className="pa-page">
        <main className="pa-body pa-body--stop">
          <span className="pa-eyebrow">{role.label.toUpperCase()} · {difficultyLabel?.toUpperCase()}</span>
          <h1 className="pa-stop-heading pa-stop-heading--small">
            You&rsquo;ve completed all the activities for this role at this level.
          </h1>
          <p className="pa-stop-subheading">Everything you did is on your dashboard. Here is where you could go next.</p>
          {runOutChoices}
        </main>
      </div>
    </>
  )

  if (step === 'setup') return (
    <>
      <TopNav />
      <div className="pa-page">
        <main className="pa-body pa-body--setup">
          <h1 className="pa-stop-heading pa-stop-heading--small">Set up your practice</h1>
          <p className="pa-stop-subheading">Choose how challenging you&rsquo;d like this practice to be.</p>

          <h2 className="pa-setup-label">How challenging would you like it to be?</h2>
          <div className="pa-setup-grid" role="radiogroup" aria-label="Difficulty">
            {DIFFICULTIES.map((option) => {
              const isActive = difficulty === option.value
              return (
                <button
                  type="button"
                  key={option.value}
                  role="radio"
                  aria-checked={isActive}
                  className={`pa-setup-card ${isActive ? 'pa-setup-card--active' : ''}`}
                  onClick={() => setDifficulty(option.value)}
                >
                  <span className="pa-setup-card-top">
                    <strong>{option.label}</strong>
                    <span className={`pa-radio ${isActive ? 'pa-radio--on' : ''}`}>
                      {isActive && <CheckIcon size={11} />}
                    </span>
                  </span>
                  <span className="pa-setup-caption">{option.caption}</span>
                </button>
              )
            })}
          </div>
        </main>
        <div className="pa-footer">
          <span className="pa-footer-note">
            {difficulty ? `${difficultyLabel} selected. You can change this next time.` : 'Choose a difficulty to continue.'}
          </span>
          <button type="button" className="pa-btn-primary" disabled={!difficulty} onClick={startPractice}>
            Continue <ArrowRightIcon size={16} />
          </button>
        </div>
      </div>
    </>
  )

  // AC 4.1.4: practice focus, skills she'll use and difficulty - no time
  // estimate, and nothing about the situations she will meet.
  if (step === 'prep') return (
    <>
      <TopNav />
      <div className="pa-page">
        <main className="pa-body">
          <h1 className="pa-stop-heading pa-stop-heading--small">Your practice</h1>
          <p className="pa-prep-subtitle">{role.label} · {difficultyLabel}</p>

          <div className="pa-columns pa-columns--prep">
            <div className="pa-card">
              <div className="pa-prep-section">
                <span className="pa-prep-label">TODAY&rsquo;S FOCUS</span>
                <h2 className="pa-prep-focus">{focusSkill || `Working as a ${role.label}`}</h2>
              </div>
              {skillsUsed.length > 0 && (
                <div className="pa-prep-section">
                  <span className="pa-prep-label">YOU&rsquo;LL USE</span>
                  <div className="pa-prep-pills">
                    {skillsUsed.map((skill) => <span key={skill} className="pa-prep-pill">{skill}</span>)}
                  </div>
                </div>
              )}
              <div className="pa-prep-section">
                <span className="pa-prep-label">YOU&rsquo;LL PRACTISE</span>
                <p className="pa-prep-text">
                  Handling the everyday situations a {role.label} meets with colleagues and stakeholders.
                </p>
              </div>
              <div className="pa-prep-section">
                <span className="pa-prep-label">DIFFICULTY</span>
                <strong className="pa-prep-value">{difficultyLabel}</strong>
              </div>
            </div>

            <div className="pa-card">
              <span className="pa-prep-label">BEFORE YOU GO IN</span>
              <div className="pa-before-item">
                <strong>Work arrives one thing at a time</strong>
                <p>You will see what each task involves when you get there.</p>
              </div>
              <div className="pa-before-item">
                <strong>Nothing is graded</strong>
                <p>You get feedback on what worked and what to consider, never a score.</p>
              </div>
              <div className="pa-before-item">
                <strong>One activity at a time</strong>
                <p>Finish the one you start. If you leave part-way, you pick it up where you left off.</p>
              </div>
            </div>
          </div>
        </main>
        <div className="pa-footer">
          <span className="pa-footer-note">
            {mayRepeat ? MAY_REPEAT : 'Once you start an activity, finish it before starting another.'}
          </span>
          <button type="button" className="pa-btn-primary" onClick={() => setStep('workplace')}>
            Enter Workplace <ArrowRightIcon size={16} />
          </button>
        </div>
      </div>
    </>
  )

  if (step === 'workplace' && floor) {
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
                      style={{ width: `${(completedCount / total) * 100}%` }}
                    />
                  </div>
                  <span className="ws-progress-label">{completedCount} of {total}</span>
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
              <p className="ws-scenario-banner-text">{floor.announcement}</p>
              <span className="ws-scenario-banner-hint">You will see what it involves when you get there.</span>
            </div>
          )}

          <div className={`ws-workplace-canvas ${isPanelOpen ? 'pa-canvas--dimmed' : ''}`}>
            <img src={workplaceImg} alt="Your workplace" className="ws-workplace-image" />
            {WORKPLACE_AREAS.map((item) => {
              const isCurrent = item.id === area.id
              const isDone = !isCurrent && doneAreaIds.includes(item.id)
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
                <h2 className="ws-area-panel-title">{floor.panel.title}</h2>
                <p className="ws-area-panel-text">{floor.panel.text}</p>
                <div className="ws-area-panel-actions">
                  <button type="button" className="ws-intro-continue" onClick={openActivity}>
                    {floor.panel.cta} <span aria-hidden="true">→</span>
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
      <div className="pa-page">
        <div className="pa-intro-hero" style={{ backgroundImage: `linear-gradient(90deg, rgba(13, 22, 40, 0.92) 0%, rgba(13, 22, 40, 0.55) 55%, rgba(13, 22, 40, 0.2) 100%), url(${introImg})` }}>
          <h1>Welcome to your practice area</h1>
          <p>You&rsquo;ll work through a realistic workplace situation based on your selected role and experience.</p>
        </div>
        <main className="pa-body">
          <h2 className="pa-setup-label">How it works</h2>
          <div className="pa-setup-grid">
            {HOW_IT_WORKS.map((item) => (
              <div key={item.number} className="pa-how-card">
                <span className="pa-how-number">{item.number}</span>
                <p>{item.text}</p>
              </div>
            ))}
          </div>
          <p className="pa-intro-note">
            Nothing here is graded. Your practice is designed to help you reconnect with your existing experience
            while exploring what has changed.
          </p>
        </main>
        <div className="pa-footer">
          <span className="pa-footer-note">Next: choose your challenge level.</span>
          <button type="button" className="pa-btn-primary" onClick={() => setStep('setup')}>
            Continue <ArrowRightIcon size={16} />
          </button>
        </div>
      </div>
    </>
  )
}
