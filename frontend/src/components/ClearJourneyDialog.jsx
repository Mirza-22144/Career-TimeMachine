import "../styles/AccessTokenModal.css";

/**
 * "Clear your journey?" confirmation (AC 3.5.2). Clear and Cancel per the
 * AC's exact dialog copy - this is destructive and irreversible, so Clear
 * uses the destructive styling, not the usual primary gradient button.
 */
export default function ClearJourneyDialog({ onClear, onCancel, isClearing, error }) {
  return (
    <div className="atm-overlay" onClick={isClearing ? undefined : onCancel}>
      <div
        className="atm-modal atm-modal--compact"
        role="dialog"
        aria-modal="true"
        aria-labelledby="cjd-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="atm-title" id="cjd-title">
          Clear your journey?
        </h2>
        <p className="atm-subtitle">This will permanently delete your journey and your token will stop working.</p>

        {error && <p className="atm-field-error">{error}</p>}

        <div className="atm-actions-row">
          <button type="button" className="atm-btn-outline" onClick={onCancel} disabled={isClearing}>
            Cancel
          </button>
          <button type="button" className="atm-btn-destructive" onClick={onClear} disabled={isClearing}>
            {isClearing ? "Clearing…" : "Clear"}
          </button>
        </div>
      </div>
    </div>
  );
}
