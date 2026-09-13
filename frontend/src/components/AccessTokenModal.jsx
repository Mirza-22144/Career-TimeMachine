import "../styles/AccessTokenModal.css";
import { PlusIcon, RefreshIcon } from "./icons";

/**
 * "Access Your Journey" modal (AC 3.1.1). Shown when the user selects
 * Generate/Access Token from the nav or Enter My Journey on the Hero.
 * This step only covers displaying the modal and its two options - the
 * Generate Token and Start My Journey buttons are not wired up yet
 * (later ACs cover actually generating/validating a token).
 */
export default function AccessTokenModal({ onClose }) {
  return (
    <div className="atm-overlay" onClick={onClose}>
      <div
        className="atm-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="atm-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="atm-header">
          <h2 className="atm-title" id="atm-title">
            Access Your Journey
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
          Generate a new token to start your journey, or enter an existing
          token to return to your saved journey.
        </p>

        <div className="atm-panel atm-panel--new">
          <div className="atm-panel-header">
            <span className="atm-panel-icon atm-panel-icon--new">
              <PlusIcon size={14} />
            </span>
            <span className="atm-panel-title">Start a new journey</span>
          </div>
          <p className="atm-panel-text">
            We&rsquo;ll create a token that keeps your progress safe.
          </p>
          <button type="button" className="atm-btn-primary">
            Generate Token
          </button>
        </div>

        <div className="atm-divider">
          <span>or</span>
        </div>

        <div className="atm-panel atm-panel--existing">
          <div className="atm-panel-header">
            <span className="atm-panel-icon atm-panel-icon--existing">
              <RefreshIcon size={14} color="#7C3AED" />
            </span>
            <span className="atm-panel-title">Come back to your journey</span>
          </div>
          <label className="atm-label" htmlFor="atm-token-input">
            Access Token
          </label>
          <input
            id="atm-token-input"
            type="text"
            className="atm-input"
            placeholder="Enter your access token"
          />
          <p className="atm-hint">Your token looks like CTM-XXXX-XXXX</p>
          <button type="button" className="atm-btn-primary">
            Start My Journey
          </button>
        </div>
      </div>
    </div>
  );
}
