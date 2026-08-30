import { useState } from 'react'
import '../styles/YourExperience.css'
import OnboardingSidebar from '../components/OnboardingSidebar'
import ExperienceSummaryCard from '../components/ExperienceSummaryCard'
import { stepTwoData } from '../mockData/onboardingData'
import { getOnboardingProfile, saveOnboardingProfile } from '../onboardingState.js'
import { navigate } from '../navigate.js'
import { CheckIcon, ArrowRightIcon } from '../components/icons'

/**
 * "Your Experience" — step 2 of the onboarding wizard. Collects the
 * technologies/tools the user has used and their main responsibilities.
 * Nothing is pre-selected — the user builds this list themselves, including
 * adding their own entries via "+ Add skill" / "+ Add responsibility".
 */
export default function YourExperience() {
  const [profile] = useState(getOnboardingProfile)
  const savedSkills = profile.skills || []
  const savedResponsibilities = profile.responsibilities || []

  // Restores prior answers if the user navigated back to fix something.
  const [selectedSkills, setSelectedSkills] = useState(savedSkills)
  const [customSkills, setCustomSkills] = useState(savedSkills.filter((s) => !stepTwoData.skills.includes(s)))
  const [isAddingSkill, setIsAddingSkill] = useState(false)
  const [skillDraft, setSkillDraft] = useState('')
  const [skillError, setSkillError] = useState('')

  const [selectedResponsibilities, setSelectedResponsibilities] = useState(savedResponsibilities)
  const [customResponsibilities, setCustomResponsibilities] = useState(
    savedResponsibilities.filter((r) => !stepTwoData.responsibilities.includes(r)),
  )
  const [isAddingResponsibility, setIsAddingResponsibility] = useState(false)
  const [responsibilityDraft, setResponsibilityDraft] = useState('')
  const [responsibilityError, setResponsibilityError] = useState('')

  const allSkills = [...stepTwoData.skills, ...customSkills]
  const allResponsibilities = [...stepTwoData.responsibilities, ...customResponsibilities]

  const toggleSkill = (skill) => {
    setSelectedSkills((prev) => (prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]))
  }

  const toggleResponsibility = (item) => {
    setSelectedResponsibilities((prev) =>
      prev.includes(item) ? prev.filter((r) => r !== item) : [...prev, item],
    )
  }

  const commitSkillDraft = () => {
    const trimmed = skillDraft.trim()
    if (!trimmed) {
      setSkillError('Please enter a skill.')
      return
    }
    if (!allSkills.includes(trimmed)) {
      setCustomSkills((prev) => [...prev, trimmed])
    }
    setSelectedSkills((prev) => (prev.includes(trimmed) ? prev : [...prev, trimmed]))
    setSkillDraft('')
    setSkillError('')
    setIsAddingSkill(false)
  }

  const cancelSkillDraft = () => {
    setSkillDraft('')
    setSkillError('')
    setIsAddingSkill(false)
  }

  const commitResponsibilityDraft = () => {
    const trimmed = responsibilityDraft.trim()
    if (!trimmed) {
      setResponsibilityError('Please enter a responsibility.')
      return
    }
    if (!allResponsibilities.includes(trimmed)) {
      setCustomResponsibilities((prev) => [...prev, trimmed])
    }
    setSelectedResponsibilities((prev) => (prev.includes(trimmed) ? prev : [...prev, trimmed]))
    setResponsibilityDraft('')
    setResponsibilityError('')
    setIsAddingResponsibility(false)
  }

  const cancelResponsibilityDraft = () => {
    setResponsibilityDraft('')
    setResponsibilityError('')
    setIsAddingResponsibility(false)
  }

  return (
    <div className="ye-page">
      <OnboardingSidebar currentStep={2} showPhoto={false} />

      <main className="ye-form-panel">
        <div className="ye-form-content">
          <span className="ye-eyebrow">{stepTwoData.eyebrow}</span>
          <h1 className="ye-heading">{stepTwoData.heading}</h1>
          <p className="ye-subheading">{stepTwoData.subheading}</p>

          <section className="ye-question">
            <div className="ye-question-header">
              <h2 className="ye-question-label">{stepTwoData.skillsLabel}</h2>
              <span className="ye-selected-count">{selectedSkills.length} selected</span>
            </div>

            <div className="ye-pill-grid">
              {allSkills.map((skill) => {
                const isActive = selectedSkills.includes(skill)
                return (
                  <button
                    type="button"
                    key={skill}
                    className={`ye-pill ${isActive ? 'ye-pill--active' : ''}`}
                    onClick={() => toggleSkill(skill)}
                    aria-pressed={isActive}
                  >
                    {isActive && <CheckIcon size={11} color="#FFFFFF" />}
                    {skill}
                  </button>
                )
              })}

              {isAddingSkill ? (
                <input
                  type="text"
                  autoFocus
                  className="ye-pill-input"
                  placeholder="Type a skill..."
                  value={skillDraft}
                  onChange={(e) => {
                    setSkillDraft(e.target.value)
                    setSkillError('')
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') commitSkillDraft()
                    if (e.key === 'Escape') cancelSkillDraft()
                  }}
                  onBlur={() => (skillDraft.trim() ? commitSkillDraft() : cancelSkillDraft())}
                />
              ) : (
                <button type="button" className="ye-pill ye-pill--add" onClick={() => setIsAddingSkill(true)}>
                  + Add skill
                </button>
              )}
            </div>
            {skillError && <p className="ye-error">{skillError}</p>}

            <p className="ye-quote">&ldquo;{stepTwoData.skillsQuote}&rdquo;</p>
          </section>

          <section className="ye-question">
            <div className="ye-question-header">
              <h2 className="ye-question-label">{stepTwoData.responsibilitiesLabel}</h2>
              <span className="ye-selected-count">{selectedResponsibilities.length} selected</span>
            </div>

            <div className="ye-responsibility-grid">
              {allResponsibilities.map((item) => {
                const isActive = selectedResponsibilities.includes(item)
                return (
                  <button
                    type="button"
                    key={item}
                    className={`ye-responsibility ${isActive ? 'ye-responsibility--active' : ''}`}
                    onClick={() => toggleResponsibility(item)}
                    aria-pressed={isActive}
                  >
                    <span className={`ye-checkbox ${isActive ? 'ye-checkbox--active' : ''}`}>
                      {isActive && <CheckIcon size={11} color="#FFFFFF" />}
                    </span>
                    {item}
                  </button>
                )
              })}

              {isAddingResponsibility ? (
                <input
                  type="text"
                  autoFocus
                  className="ye-responsibility-input"
                  placeholder="Type a responsibility..."
                  value={responsibilityDraft}
                  onChange={(e) => {
                    setResponsibilityDraft(e.target.value)
                    setResponsibilityError('')
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') commitResponsibilityDraft()
                    if (e.key === 'Escape') cancelResponsibilityDraft()
                  }}
                  onBlur={() => (responsibilityDraft.trim() ? commitResponsibilityDraft() : cancelResponsibilityDraft())}
                />
              ) : (
                <button
                  type="button"
                  className="ye-responsibility ye-responsibility--add"
                  onClick={() => setIsAddingResponsibility(true)}
                >
                  + Add responsibility
                </button>
              )}
            </div>
            {responsibilityError && <p className="ye-error">{responsibilityError}</p>}
          </section>

          <div className="ye-translate-note">{stepTwoData.translateNote}</div>

          <button
            type="button"
            className="ye-continue"
            disabled={selectedSkills.length === 0}
            onClick={() => {
              saveOnboardingProfile({ skills: selectedSkills, responsibilities: selectedResponsibilities })
              navigate('/your-break')
            }}
          >
            {stepTwoData.ctaLabel}
            <ArrowRightIcon size={16} />
          </button>
        </div>
      </main>

      <ExperienceSummaryCard
        role={profile.role}
        years={profile.years}
        skills={selectedSkills}
        responsibilities={selectedResponsibilities}
      />
    </div>
  )
}
