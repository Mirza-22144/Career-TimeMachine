import "../styles/AccessTokenModal.css";

/**
 * Small "Access token required" notice. Shown when Maya selects a
 * token-dependent nav item (Career Journey, Practice Scenarios, ePortfolio)
 * without an active token. Dismissing it leaves her on the current page -
 * it never navigates anywhere itself.
 */
export default function TokenRequiredModal({ onClose }) {
  return (
    <div className="atm-overlay" onClick={onClose}>
      <div
        className="atm-modal atm-modal--compact"
        role="dialog"
        aria-modal="true"
        aria-labelledby="trm-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="atm-header">
          <h2 className="atm-title" id="trm-title">
            Access token required
          </h2>
          <button
            type="button"
            className="atm-close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <p className="atm-subtitle">
          Generate or enter an access token to continue.
        </p>
        <button type="button" className="atm-btn-primary atm-btn-okay" onClick={onClose}>
          Okay
        </button>
      </div>
    </div>
  );
}
