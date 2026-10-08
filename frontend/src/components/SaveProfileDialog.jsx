import "../styles/AccessTokenModal.css";

/**
 * "Save your career profile?" confirmation (AC 3.2.4). Shown the first
 * time Maya finishes the wizard, before the profile is actually saved -
 * Cancel ("Not yet") closes this and leaves her on Your Break with her
 * entries kept; Save My Profile runs the real save.
 */
export default function SaveProfileDialog({ onSave, onCancel, isSaving, error }) {
  return (
    <div className="atm-overlay" onClick={isSaving ? undefined : onCancel}>
      <div
        className="atm-modal atm-modal--compact"
        role="dialog"
        aria-modal="true"
        aria-labelledby="spd-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="atm-title" id="spd-title">
          Save your career profile?
        </h2>
        <p className="atm-subtitle">
          We will save your story, experience and break to your access token. You can change any of it later from
          Career Profile.
        </p>

        {error && <p className="atm-field-error">{error}</p>}

        <div className="atm-actions-row">
          <button type="button" className="atm-btn-primary" onClick={onSave} disabled={isSaving}>
            {isSaving ? "Saving…" : "Save my profile"}
          </button>
          <button type="button" className="atm-btn-outline" onClick={onCancel} disabled={isSaving}>
            Not yet
          </button>
        </div>
      </div>
    </div>
  );
}
