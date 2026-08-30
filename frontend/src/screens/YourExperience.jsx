import { useEffect, useState } from 'react'
import '../styles/YourExperience.css'
import OnboardingSidebar from '../components/OnboardingSidebar'
import ExperienceSummaryCard from '../components/ExperienceSummaryCard'
import { stepTwoData } from '../mockData/onboardingData'
import { api } from '../api.js'
import { navigate } from '../navigate.js'
import { CheckIcon, ArrowRightIcon } from '../components/icons'

/**
 * "Your Experience" — step 2. Technologies/tools and responsibilities come
 * from the backend catalogue (GET /catalogue/skills, /responsibilities);
 * "+ Add" entries are free text, saved as custom_skills/custom_responsibilities.
 */
export default function YourExperience() {
  const [loading, setLoading] = useState(true)
  const [catalogueSkills, setCatalogueSkills] = useState([])
  const [catalogueResponsibilities, setCatalogueResponsibilities] = useState([])
  const [roles, setRoles] = useState([])
  const [experienceOptions, setExperienceOptions] = useState([])
  const [profile, setProfile] = useState(null)

  const [selectedSkillIds, setSelectedSkillIds] = useState([])
  const [customSkills, setCustomSkills] = useState([])
  const [isAddingSkill, setIsAddingSkill] = useState(false)
  const [skillDraft, setSkillDraft] = useState('')
  const [skillError, setSkillError] = useState('')

  const [selectedResponsibilityIds, setSelectedResponsibilityIds] = useState([])
  const [customResponsibilities, setCustomResponsibilities] = useState([])
  const [isAddingResponsibility, setIsAddingResponsibility] = useState(false)
  const [responsibilityDraft, setResponsibilityDraft] = useState('')
  const [responsibilityError, setResponsibilityError] = useState('')

  useEffect(() => {
    async function load() {
      const [skills, responsibilities, rolesData, experienceData, profileData] = await Promise.all([
        api.getCatalogue('skills'),
        api.getCatalogue('responsibilities'),
        api.getCatalogue('roles'),
        api.getCatalogue('experience-options'),
        api.getProfile(),
      ])
      setCatalogueSkills(skills)
      setCatalogueResponsibilities(responsibilities)
      setRoles(rolesData)
      setExperienceOptions(experienceData)
      setProfile(profileData)
      setSelectedSkillIds(profileData.skill_ids || [])
      setCustomSkills(profileData.custom_skills || [])
      setSelectedResponsibilityIds(profileData.responsibility_ids || [])
      setCustomResponsibilities(profileData.custom_responsibilities || [])
      setLoading(false)
    }
    load()
  }, [])

  const toggleSkill = (id) => {
    setSelectedSkillIds((prev) => (prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]))
  }

  const toggleResponsibility = (id) => {
    setSelectedResponsibilityIds((prev) => (prev.includes(id) ? prev.filter((r) => r !== id) : [...prev, id]))
  }

  const commitSkillDraft = () => {
    const trimmed = skillDraft.trim()
    if (!trimmed) {
      setSkillError('Please enter a skill.')
      return
    }
    if (!customSkills.includes(trimmed)) setCustomSkills((prev) => [...prev, trimmed])
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
    if (!customResponsibilities.includes(trimmed)) setCustomResponsibilities((prev) => [...prev, trimmed])
    setResponsibilityDraft('')
    setResponsibilityError('')
    setIsAddingResponsibility(false)
  }

  const cancelResponsibilityDraft = () => {
    setResponsibilityDraft('')
    setResponsibilityError('')
    setIsAddingResponsibility(false)
  }

  const handleContinue = async () => {
    await api.patchProfile({
      skill_ids: selectedSkillIds,
      custom_skills: customSkills,
      responsibility_ids: selectedResponsibilityIds,
      custom_responsibilities: customResponsibilities,
    })
    navigate('/your-break')
  }

  if (loading) return <div className="ye-page" />

  const skillLabel = (id) => catalogueSkills.find((s) => s.id === id)?.label || id
  const responsibilityLabel = (id) => catalogueResponsibilities.find((r) => r.id === id)?.label || id
  const selectedSkillLabels = [...selectedSkillIds.map(skillLabel), ...customSkills]
  const selectedResponsibilityLabels = [...selectedResponsibilityIds.map(responsibilityLabel), ...customResponsibilities]

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
              <span className="ye-selected-count">{selectedSkillLabels.length} selected</span>
            </div>

            <div className="ye-pill-grid">
              {catalogueSkills.map((skill) => {
                const isActive = selectedSkillIds.includes(skill.id)
                return (
                  <button
                    type="button"
                    key={skill.id}
                    className={`ye-pill ${isActive ? 'ye-pill--active' : ''}`}
                    onClick={() => toggleSkill(skill.id)}
                    aria-pressed={isActive}
                  >
                    {isActive && <CheckIcon size={11} color="#FFFFFF" />}
                    {skill.label}
                  </button>
                )
              })}
              {customSkills.map((skill) => (
                <button type="button" key={skill} className="ye-pill ye-pill--active" onClick={() => setCustomSkills((prev) => prev.filter((s) => s !== skill))}>
                  <CheckIcon size={11} color="#FFFFFF" />
                  {skill}
                </button>
              ))}

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
              <span className="ye-selected-count">{selectedResponsibilityLabels.length} selected</span>
            </div>

            <div className="ye-responsibility-grid">
              {catalogueResponsibilities.map((item) => {
                const isActive = selectedResponsibilityIds.includes(item.id)
                return (
                  <button
                    type="button"
                    key={item.id}
                    className={`ye-responsibility ${isActive ? 'ye-responsibility--active' : ''}`}
                    onClick={() => toggleResponsibility(item.id)}
                    aria-pressed={isActive}
                  >
                    <span className={`ye-checkbox ${isActive ? 'ye-checkbox--active' : ''}`}>
                      {isActive && <CheckIcon size={11} color="#FFFFFF" />}
                    </span>
                    {item.label}
                  </button>
                )
              })}
              {customResponsibilities.map((item) => (
                <button
                  type="button"
                  key={item}
                  className="ye-responsibility ye-responsibility--active"
                  onClick={() => setCustomResponsibilities((prev) => prev.filter((r) => r !== item))}
                >
                  <span className="ye-checkbox ye-checkbox--active">
                    <CheckIcon size={11} color="#FFFFFF" />
                  </span>
                  {item}
                </button>
              ))}

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
            disabled={selectedSkillLabels.length === 0}
            onClick={handleContinue}
          >
            {stepTwoData.ctaLabel}
            <ArrowRightIcon size={16} />
          </button>
        </div>
      </main>

      <ExperienceSummaryCard
        role={profile?.role_other_text || roles.find((r) => r.id === profile?.role_id)?.label}
        experienceLabel={experienceOptions.find((y) => y.id === profile?.years_experience)?.label}
        skills={selectedSkillLabels}
        responsibilities={selectedResponsibilityLabels}
      />
    </div>
  )
}
