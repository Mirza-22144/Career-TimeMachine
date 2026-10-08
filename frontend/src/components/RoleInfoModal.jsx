import { useEffect } from "react";
import "../styles/RoleInfoModal.css";
import { MOCK_OUTLOOK_SOURCE, mockOutlook, mockRelation } from "../mockData/roadmapData.js";

const monthYear = (iso) => new Date(iso).toLocaleDateString("en-AU", { month: "long", year: "numeric" });

/**
 * Role information panel (AC 2.4.1), opened from the "i" on a roadmap
 * card. The vacancy range, source and date are real (GET /roadmap); the
 * outlook and relationship text are mock for now - see
 * mockData/roadmapData.js. Closes on the Close button, an outside click
 * or Escape.
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

        <span className="rim-label">OUTLOOK TO 2035</span>
        <p className="rim-text">{mockOutlook(role.role_label)}</p>
        <span className="rim-source">{MOCK_OUTLOOK_SOURCE}</span>

        {!isPrevious && (
          <>
            <span className="rim-label rim-label--spaced">HOW IT RELATES TO {previousRoleLabel.toUpperCase()}</span>
            <p className="rim-text">{mockRelation(role.role_label, previousRoleLabel)}</p>
          </>
        )}
      </div>
    </div>
  );
}
