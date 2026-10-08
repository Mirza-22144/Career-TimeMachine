import { useState } from "react";
import "../styles/ClosestRoleDialog.css";

/**
 * "Which role is closest to this job?" (AC 5.2.2). Shows the closest
 * roles with the closest preselected, or - via See all roles - every role
 * in the role catalogue, alphabetically. With no close role it becomes the "We don't have
 * a roadmap for this kind of role yet." notice instead.
 */
export default function ClosestRoleDialog({ closest, allRoles, onConfirm, onBack, onExploreRoles, isSaving, error }) {
  const [showAll, setShowAll] = useState(false);
  const [selectedId, setSelectedId] = useState(closest[0]?.role_id || null);

  if (closest.length === 0 && !showAll) {
    return (
      <div className="crd-overlay" onClick={onBack}>
        <div className="crd-modal" role="dialog" aria-modal="true" aria-labelledby="crd-title" onClick={(e) => e.stopPropagation()}>
          <h2 className="crd-title" id="crd-title">We don&rsquo;t have a roadmap for this kind of role yet.</h2>
          <p className="crd-text">
            Your map for this job is still saved. You can explore roles that match your experience, or pick a role
            yourself.
          </p>
          <button type="button" className="crd-link" onClick={() => setShowAll(true)}>See all roles</button>
          <div className="crd-actions">
            <button type="button" className="crd-btn-outline" onClick={onBack}>Back to my map</button>
            <button type="button" className="crd-btn-primary" onClick={onExploreRoles}>Explore roles</button>
          </div>
        </div>
      </div>
    );
  }

  const renderOption = (role, isClosest) => {
    const isSelected = role.role_id === selectedId;
    return (
      <button
        key={role.role_id}
        type="button"
        role="radio"
        aria-checked={isSelected}
        className={`${showAll ? "crd-all-option" : "crd-option"} ${isSelected ? "is-selected" : ""}`}
        onClick={() => setSelectedId(role.role_id)}
      >
        <span className={`crd-radio ${isSelected ? "crd-radio--on" : ""}`} />
        <span className="crd-option-label">{role.role_label}</span>
        {isClosest && <span className="crd-closest">Closest to this ad</span>}
      </button>
    );
  };

  return (
    <div className="crd-overlay" onClick={isSaving ? undefined : onBack}>
      <div
        className={`crd-modal ${showAll ? "crd-modal--wide" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="crd-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="crd-title" id="crd-title">Which role is closest to this job?</h2>
        <p className="crd-text">
          {showAll
            ? "Pick the closest one and we’ll build your roadmap from it."
            : "Job titles vary between companies. Pick the closest one and we’ll build your roadmap from it."}
        </p>

        <div className={showAll ? "crd-all" : "crd-options"} role="radiogroup" aria-label="Closest role">
          {(showAll ? allRoles : closest).map((role, index) => renderOption(role, !showAll && index === 0))}
        </div>

        {!showAll && (
          <button type="button" className="crd-link" onClick={() => setShowAll(true)}>See all roles</button>
        )}

        {error && <p className="crd-error">{error}</p>}

        <div className="crd-actions">
          <button type="button" className="crd-btn-outline" onClick={onBack} disabled={isSaving}>Back</button>
          <button
            type="button"
            className="crd-btn-primary"
            disabled={!selectedId || isSaving}
            onClick={() => onConfirm(selectedId)}
          >
            {isSaving ? "Opening…" : "Open my roadmap"}
          </button>
        </div>
      </div>
    </div>
  );
}
