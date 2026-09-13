import { useState } from "react";
import "../styles/AccessTokenModal.css";
import { PlusIcon, RefreshIcon } from "./icons";
import { isKnownToken, setActiveToken } from "../accessToken.js";

/**
 * "Access Your Journey" modal (AC 3.1.1). Shown when the user selects
 * Generate/Access Token from the nav or Enter My Journey on the Hero.
 * Generate Token (AC 3.1.2) hands off to the generated-token modal via
 * onGenerateToken. The existing-token path validates against tokens
 * generated this session (see accessToken.js) - swap for a real backend
 * lookup once BE 3.x exists.
 */
export default function AccessTokenModal({ onClose, onGenerateToken, onValidToken }) {
  const [existingToken, setExistingToken] = useState("");
  // null | "empty" | "invalid"
  const [tokenError, setTokenError] = useState(null);

  const handleChange = (e) => {
    setExistingToken(e.target.value);
    setTokenError(null);
  };

  const handleStartMyJourney = () => {
    const trimmed = existingToken.trim();
    if (!trimmed) {
      setTokenError("empty");
      return;
    }
    if (!isKnownToken(trimmed)) {
      setTokenError("invalid");
      return;
    }
    setActiveToken(trimmed);
    setTokenError(null);
    onValidToken();
  };

  const handleTryAgain = () => {
    setExistingToken("");
    setTokenError(null);
  };

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
          <button type="button" className="atm-btn-primary" onClick={onGenerateToken}>
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
            className={`atm-input ${tokenError ? "atm-input--error" : ""}`}
            placeholder="Enter your access token"
            value={existingToken}
            onChange={handleChange}
          />
          {tokenError === "empty" && (
            <p className="atm-field-error">
              <span className="atm-field-error-icon">!</span>
              Please enter your access token to continue.
            </p>
          )}
          {tokenError === "invalid" && (
            <p className="atm-field-error">
              <span className="atm-field-error-icon">!</span>
              That token isn&rsquo;t recognised. Please check it and try again.
            </p>
          )}
          {tokenError !== "invalid" && (
            <p className="atm-hint">Your token looks like CTM-XXXX-XXXX</p>
          )}

          <div className="atm-actions-row">
            <button type="button" className="atm-btn-primary" onClick={handleStartMyJourney}>
              Start My Journey
            </button>
            {tokenError === "invalid" && (
              <button type="button" className="atm-btn-outline" onClick={handleTryAgain}>
                Try Again
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
