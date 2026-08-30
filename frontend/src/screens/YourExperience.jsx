import { useEffect, useState } from 'react'
import '../styles/YourExperience.css'
import OnboardingSidebar from '../components/OnboardingSidebar'
import ExperienceSummaryCard from '../components/ExperienceSummaryCard'
import { stepTwoData } from '../mockData/onboardingData'
import { api } from '../api.js'
import { navigate } from '../navigate.js'
import { CheckIcon, ArrowRightIcon } from '../components/icons'

// Real skill catalogues can run into the hundreds per role (DATA_HANDOVER.md
// 5.1). Only the top 10 (already in_demand/hot_technology-sorted by the
// backend) show as default suggestions; search or "+ Add skill" reach
// anything beyond that - never a full browse list.
const DEFAULT_SUGGESTIONS = 10
const MAX_SUGGESTIONS = 8

/**
 * "Your Experience" — step 2. Responsibilities come from the backend
 * catalogue (GET /catalogue/responsibilities); skills depend on the role
 * chosen in step 1 (GET /catalogue/skills?role_id=...). "+ Add" entries are
 * free text unless they match a catalogue skill, saved as
 * custom_skills/custom_responsibilities.
 */
export default function YourExperience() {
  const [loading, setLoading] = useState(true)
  const [catalogueSkills, setCatalogueSkills] = useState([])
  const [allSkills, setAllSkills] = useState([])
  const [catalogueResponsibilities, setCatalogueResponsibilities] = useState([])
  const [roles, setRoles] = useState([])
  const [experienceOptions, setExperienceOptions] = useState([])
  const [profile, setProfile] = useState(null)

  const [selectedSkillIds, setSelectedSkillIds] = useState([])
  const [customSkills, setCustomSkills] = useState([])
  const [isAddingSkill, setIsAddingSkill] = useState(false)
  const [skillDraft, setSkillDraft] = useState('')
  const [skillError, setSkillError] = useState('')
  const [skillSearch, setSkillSearch] = useState('')

  const [selectedResponsibilityIds, setSelectedResponsibilityIds] = useState([])
  const [customResponsibilities, setCustomResponsibilities] = useState([])
  const [isAddingResponsibility, setIsAddingResponsibility] = useState(false)
  const [responsibilityDraft, setResponsibilityDraft] = useState('')
  const [responsibilityError, setResponsibilityError] = useState('')

  useEffect(() => {
    async function load() {
      const [responsibilities, rolesData, experienceData, profileData] = await Promise.all([
        api.getCatalogue('responsibilities'),
        api.getCatalogue('roles'),
        api.getCatalogue('experience-options'),
        api.getProfile(),
      ])
      // Role-scoped list drives the default 10 suggestions (AC 1.2.1's
      // "relevant" set); the full catalogue backs search/"+ Add skill" so a
      // real skill is always findable even if it isn't linked to this role.
      const [skills, everySkill] = await Promise.all([
        api.getSkills(profileData.role_id),
        api.getCatalogue('skills'),
      ])
      setCatalogueSkills(skills)
      setAllSkills(everySkill)
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

  // Enter commits the draft: a catalogue match gets selected (not duplicated
  // as free text), anything else becomes a custom skill.
  const commitSkillDraft = () => {
    const trimmed = skillDraft.trim()
    if (!trimmed) {
      setSkillError('Please enter a skill.')
      return
    }
    const match = allSkills.find((s) => s.label.toLowerCase() === trimmed.toLowerCase())
    if (match) {
      if (!selectedSkillIds.includes(match.id)) toggleSkill(match.id)
    } else if (!customSkills.includes(trimmed)) {
      setCustomSkills((prev) => [...prev, trimmed])
    }
    setSkillDraft('')
    setSkillError('')
    setIsAddingSkill(false)
  }

  const cancelSkillDraft = () => {
    setSkillDraft('')
    setSkillError('')
    setIsAddingSkill(false)
  }

  const selectSkillSuggestion = (skill) => {
    if (!selectedSkillIds.includes(skill.id)) toggleSkill(skill.id)
    setSkillDraft('')
    setSkillError('')
    setIsAddingSkill(false)
  }

  const selectSearchResult = (skill) => {
    if (!selectedSkillIds.includes(skill.id)) toggleSkill(skill.id)
    setSkillSearch('')
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

  const skillLabel = (id) => allSkills.find((s) => s.id === id)?.label || catalogueSkills.find((s) => s.id === id)?.label || id
  const responsibilityLabel = (id) => catalogueResponsibilities.find((r) => r.id === id)?.label || id
  const selectedSkillLabels = [...selectedSkillIds.map(skillLabel), ...customSkills]
  const selectedResponsibilityLabels = [...selectedResponsibilityIds.map(responsibilityLabel), ...customResponsibilities]

  // Both search the FULL catalogue (not just this role's list) - a real
  // skill should always be findable, even if it isn't linked to this role.
  const skillSuggestions = isAddingSkill && skillDraft.trim()
    ? allSkills
        .filter((s) => !selectedSkillIds.includes(s.id) && s.label.toLowerCase().includes(skillDraft.trim().toLowerCase()))
        .slice(0, MAX_SUGGESTIONS)
    : []
  const searchResults = skillSearch.trim()
    ? allSkills
        .filter((s) => !selectedSkillIds.includes(s.id) && s.label.toLowerCase().includes(skillSearch.trim().toLowerCase()))
        .slice(0, MAX_SUGGESTIONS)
    : []

  // Default suggestion pills: top 10 catalogue skills, plus any selected
  // skill that fell outside that top 10 (e.g. picked via search), so a
  // selection never disappears from view.
  const topSkills = catalogueSkills.slice(0, DEFAULT_SUGGESTIONS)
  const extraSelectedSkills = selectedSkillIds
    .filter((id) => !topSkills.some((s) => s.id === id))
    .map((id) => allSkills.find((s) => s.id === id) || catalogueSkills.find((s) => s.id === id))
    .filter(Boolean)
  const suggestedSkills = [...extraSelectedSkills, ...topSkills]

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

            <div className="ye-skill-search-wrap">
              <input
                type="text"
                className="ye-skill-search"
                placeholder="Search skills..."
                value={skillSearch}
                onChange={(e) => setSkillSearch(e.target.value)}
              />
              {searchResults.length > 0 && (
                <div className="ye-skill-suggestions">
                  {searchResults.map((s) => (
                    <button
                      type="button"
                      key={s.id}
                      className="ye-skill-suggestion"
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => selectSearchResult(s)}
                    >
                      {s.label}
                      {s.in_demand && <span className="ye-skill-tag">In demand</span>}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="ye-pill-grid">
              {suggestedSkills.map((skill) => {
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
                    {skill.in_demand && <span className="ye-skill-tag">In demand</span>}
                    {!skill.in_demand && skill.hot_technology && <span className="ye-skill-tag">Hot</span>}
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
                <div className="ye-skill-add">
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
                  {skillSuggestions.length > 0 && (
                    <div className="ye-skill-suggestions">
                      {skillSuggestions.map((s) => (
                        <button
                          type="button"
                          key={s.id}
                          className="ye-skill-suggestion"
                          onMouseDown={(e) => e.preventDefault()}
                          onClick={() => selectSkillSuggestion(s)}
                        >
                          {s.label}
                          {s.in_demand && <span className="ye-skill-tag">In demand</span>}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
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
