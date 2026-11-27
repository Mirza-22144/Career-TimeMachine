import { useEffect, useState } from 'react'
import '../styles/YourExperience.css'
import OnboardingSidebar from '../components/OnboardingSidebar'
import ExperienceSummaryCard from '../components/ExperienceSummaryCard'
import { stepTwoData } from '../mockData/onboardingData'
import { api } from '../api.js'
import { navigate } from '../navigate.js'
import { CheckIcon, ArrowRightIcon } from '../components/icons'

// Default pill count and search/suggestion cap, so a role with hundreds of
// linked skills never dumps a full list onto the screen.
const DEFAULT_SUGGESTIONS = 10
const MAX_SUGGESTIONS = 8

// Open/type/commit/cancel state for a "+ Add X" chip - shared by the skill
// and responsibility sections below, since both work the same way.
function useTagDraft(commitValue, emptyErrorMessage) {
  const [isOpen, setIsOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [error, setError] = useState('')

  // Updates the typed text and clears any old error.
  const change = (value) => {
    setDraft(value)
    setError('')
  }
  // Saves the typed value (via commitValue) and closes the input, or shows
  // an error if it was left blank.
  const commit = () => {
    const trimmed = draft.trim()
    if (!trimmed) {
      setError(emptyErrorMessage)
      return
    }
    commitValue(trimmed)
    setDraft('')
    setIsOpen(false)
  }
  // Closes the input without saving anything.
  const cancel = () => {
    setDraft('')
    setError('')
    setIsOpen(false)
  }

  return { isOpen, open: () => setIsOpen(true), draft, change, error, commit, cancel }
}

/**
 * Step 2 of the onboarding wizard, shown at the "/your-experience" URL.
 * Collects skills and responsibilities. Responsibilities come from the
 * backend catalogue; skills depend on the role chosen in step 1, since the
 * real catalogue is role-specific and far too large to browse flat.
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
  const [skillSearch, setSkillSearch] = useState('')

  const [selectedResponsibilityIds, setSelectedResponsibilityIds] = useState([])
  const [customResponsibilities, setCustomResponsibilities] = useState([])

  useEffect(() => {
    async function load() {
      const [responsibilities, rolesData, experienceData, profileData] = await Promise.all([
        api.getCatalogue('responsibilities'),
        api.getCatalogue('roles'),
        api.getCatalogue('experience-options'),
        api.getProfile(),
      ])
      // The list for this role drives the default suggestion pills; search
      // looks at every skill instead, so a real skill can still be found
      // even if it isn't linked to this particular role.
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

  // Adds or removes a skill id from the selected list. Used when a skill
  // pill or suggestion is clicked.
  const toggleSkill = (id) => {
    setSelectedSkillIds((prev) => (prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]))
  }

  // Adds or removes a responsibility id from the selected list. Used when
  // a responsibility pill is clicked.
  const toggleResponsibility = (id) => {
    setSelectedResponsibilityIds((prev) => (prev.includes(id) ? prev.filter((r) => r !== id) : [...prev, id]))
  }

  // A typed skill that matches a real catalogue entry gets selected
  // instead of duplicated as free text.
  const skillDraft = useTagDraft((trimmed) => {
    const match = allSkills.find((s) => s.label.toLowerCase() === trimmed.toLowerCase())
    if (match) {
      if (!selectedSkillIds.includes(match.id)) toggleSkill(match.id)
    } else if (!customSkills.includes(trimmed)) {
      setCustomSkills((prev) => [...prev, trimmed])
    }
  }, 'Please enter a skill.')

  const responsibilityDraft = useTagDraft((trimmed) => {
    if (!customResponsibilities.includes(trimmed)) setCustomResponsibilities((prev) => [...prev, trimmed])
  }, 'Please enter a responsibility.')

  // Picks a skill from the "+ Add skill" suggestion list, then closes it.
  const selectSkillSuggestion = (skill) => {
    if (!selectedSkillIds.includes(skill.id)) toggleSkill(skill.id)
    skillDraft.cancel()
  }

  // Picks a skill from the search box's result list, then clears the search.
  const selectSearchResult = (skill) => {
    if (!selectedSkillIds.includes(skill.id)) toggleSkill(skill.id)
    setSkillSearch('')
  }

  // Saves the chosen skills and responsibilities, then moves to step 3.
  // Runs when the Continue button is clicked.
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

  // Looks up a skill's display label from its id.
  const skillLabel = (id) => allSkills.find((s) => s.id === id)?.label || catalogueSkills.find((s) => s.id === id)?.label || id
  // Looks up a responsibility's display label from its id.
  const responsibilityLabel = (id) => catalogueResponsibilities.find((r) => r.id === id)?.label || id
  const selectedSkillLabels = [...selectedSkillIds.map(skillLabel), ...customSkills]
  const selectedResponsibilityLabels = [...selectedResponsibilityIds.map(responsibilityLabel), ...customResponsibilities]

  // Search and the "+ Add skill" suggestions both look across every skill,
  // not just this role's list.
  const skillSuggestions = skillDraft.isOpen && skillDraft.draft.trim()
    ? allSkills
        .filter((s) => !selectedSkillIds.includes(s.id) && s.label.toLowerCase().includes(skillDraft.draft.trim().toLowerCase()))
        .slice(0, MAX_SUGGESTIONS)
    : []
  const searchResults = skillSearch.trim()
    ? allSkills
        .filter((s) => !selectedSkillIds.includes(s.id) && s.label.toLowerCase().includes(skillSearch.trim().toLowerCase()))
        .slice(0, MAX_SUGGESTIONS)
    : []

  // Default pills: the role's top skills, plus any selection that fell
  // outside that top slice (e.g. picked via search), so it stays visible.
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

              {skillDraft.isOpen ? (
                <div className="ye-skill-add">
                  <div className="ye-tag-input-row">
                    <input
                      type="text"
                      autoFocus
                      className="ye-pill-input"
                      placeholder="Type a skill..."
                      value={skillDraft.draft}
                      onChange={(e) => skillDraft.change(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') skillDraft.commit()
                        if (e.key === 'Escape') skillDraft.cancel()
                      }}
                      onBlur={skillDraft.cancel}
                    />
                    <button
                      type="button"
                      className="ye-tag-cancel"
                      aria-label="Cancel adding a skill"
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={skillDraft.cancel}
                    >
                      ✕
                    </button>
                  </div>
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
                <button type="button" className="ye-pill ye-pill--add" onClick={skillDraft.open}>
                  + Add skill
                </button>
              )}
            </div>
            {skillDraft.error && <p className="ye-error">{skillDraft.error}</p>}

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

              {responsibilityDraft.isOpen ? (
                <div className="ye-tag-input-row ye-tag-input-row--responsibility">
                  <input
                    type="text"
                    autoFocus
                    className="ye-responsibility-input"
                    placeholder="Type a responsibility..."
                    value={responsibilityDraft.draft}
                    onChange={(e) => responsibilityDraft.change(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') responsibilityDraft.commit()
                      if (e.key === 'Escape') responsibilityDraft.cancel()
                    }}
                    onBlur={responsibilityDraft.cancel}
                  />
                  <button
                    type="button"
                    className="ye-tag-cancel"
                    aria-label="Cancel adding a responsibility"
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={responsibilityDraft.cancel}
                  >
                    ✕
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  className="ye-responsibility ye-responsibility--add"
                  onClick={responsibilityDraft.open}
                >
                  + Add responsibility
                </button>
              )}
            </div>
            {responsibilityDraft.error && <p className="ye-error">{responsibilityDraft.error}</p>}
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
