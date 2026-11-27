import '../styles/ExperienceSummaryCard.css'

/**
 * Floating "Your experience" summary card shown alongside steps 2+ of the
 * onboarding wizard. Reflects answers already collected in earlier steps
 * (role, years) plus the current step's selections (skills, responsibilities).
 */
export default function ExperienceSummaryCard({ role, experienceLabel, skills = [], responsibilities = [] }) {
  return (
    <aside className="esc-card">
      <h3 className="esc-title">Your experience</h3>

      <div className="esc-row">
        <span className="esc-label">Role</span>
        <span className="esc-value">{role || '—'}</span>
      </div>
      <div className="esc-row">
        <span className="esc-label">Experience</span>
        <span className="esc-value">{experienceLabel || '—'}</span>
      </div>
      <div className="esc-row">
        <span className="esc-label">Skills</span>
        <span className="esc-value">{skills.length} selected</span>
      </div>
      <div className="esc-row">
        <span className="esc-label">Responsibilities</span>
        <span className="esc-value">{responsibilities.length} selected</span>
      </div>

      {skills.length > 0 && (
        <div className="esc-skills">
          <span className="esc-skills-label">SKILLS</span>
          <p className="esc-skills-list">{skills.join(', ')}</p>
        </div>
      )}
    </aside>
  )
}
