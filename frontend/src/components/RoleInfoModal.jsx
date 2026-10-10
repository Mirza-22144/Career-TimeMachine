import { useEffect } from "react";
import "../styles/RoleInfoModal.css";

// "A", "A and B", "A, B and C" - at most three, so the sentence stays short.
function listLabels(skills) {
  const labels = skills.slice(0, 3).map((skill) => skill.label);
  if (labels.length <= 1) return labels[0] || "";
  return `${labels.slice(0, -1).join(", ")} and ${labels.at(-1)}`;
}

// Used when the role has no explanation from the prediction model (a role
// she picked herself, or the explainer was unavailable).
// How a suggested role relates to her previous one, said only from what
// the roadmap already knows: the skills on her profile that this role
// lists, and the ones it would add. No scores or percentages.
function relationText(role, previousRoleLabel) {
  const has = role.skills_bring_back;
  const next = role.skills_could_explore.filter((skill) => skill.status !== "practised");
  const first = has.length > 0
    ? `From your time as a ${previousRoleLabel} you already have ${listLabels(has)}, which ${has.length === 1 ? "is" : "are"} listed for ${role.role_label} roles.`
    : `None of the skills on your profile are listed for ${role.role_label} roles yet, so more of this role would be new to you.`;
  const second = next.length > 0 ? ` From there you could explore ${listLabels(next)}.` : "";
  return first + second;
}

const monthYear = (iso) => new Date(iso).toLocaleDateString("en-AU", { month: "long", year: "numeric" });

/**
 * Role information panel (AC 2.4.1), opened from the "i" on a roadmap
 * card. Everything shown comes from GET /roadmap. Closes on the Close
 * button, an outside click or Escape.
 */
export default function RoleInfoModal({ role, isPrevious, previousRoleLabel, onClose }) {
  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  const market = role.market_data;

  return (
    <div className="rim-overlay" onClick={onClose}>
      <div
        className="rim-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="rim-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="rim-header">
          <div>
            <span className="rim-eyebrow">{isPrevious ? "YOUR PREVIOUS ROLE" : "ROLE YOU COULD EXPLORE"}</span>
            <h2 className="rim-title" id="rim-title">{role.role_label}</h2>
          </div>
          <button type="button" className="rim-close" onClick={onClose} aria-label="Close" autoFocus>
            ×
          </button>
        </div>

        <div className="rim-vacancy">
          <span className="rim-label">JOB VACANCIES IN AUSTRALIA</span>
          {market ? (
            <>
              <span className="rim-range">
                {market.ads_range_low.toLocaleString()} to {market.ads_range_high.toLocaleString()}
              </span>
              <span className="rim-range-caption">Current advertised range</span>
              <span className="rim-source">
                Source: Jobs and Skills Australia, Internet Vacancy Index. As of {monthYear(market.latest_month)}.
              </span>
            </>
          ) : (
            <span className="rim-range-caption">Vacancy information isn&rsquo;t available for this role.</span>
          )}
        </div>

        {!isPrevious && (role.explanation || role.skill_data_available) && (
          <>
            <span className="rim-label">HOW IT RELATES TO {previousRoleLabel.toUpperCase()}</span>
            <p className="rim-text">{role.explanation?.summary || relationText(role, previousRoleLabel)}</p>
          </>
        )}
      </div>
    </div>
  );
}
