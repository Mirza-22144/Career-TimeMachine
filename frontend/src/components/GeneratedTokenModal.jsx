import { useState } from "react";
import "../styles/AccessTokenModal.css";
import { ShieldIcon, CheckIcon } from "./icons";
import { copyToClipboard } from "../copyToClipboard.js";

/**
 * "Your access token" modal (AC 3.1.2). Shown right after Generate Token
 * succeeds on the Access Your Journey modal - this is the one place a
 * token display also offers a way into Your Story. Viewing an already-
 * active token later (AC 3.1.5) uses MyTokenModal instead, which is
 * copy-only.
 */
export default function GeneratedTokenModal({ token, onClose, onStartJourney }) {
  const [copyState, setCopyState] = useState("idle"); // idle | copied | error

  const handleCopy = async () => {
    try {
      await copyToClipboard(token);
      setCopyState("copied");
    } catch {
      setCopyState("error");
    }
  };

  return (
    <div className="atm-overlay" onClick={onClose}>
      <div
        className="atm-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="gtm-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="atm-header">
          <h2 className="atm-title" id="gtm-title">
            Your access token
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
          This token is your journey. Use it any time you want to come back.
        </p>

        <div className="atm-token-box">
          <span className="atm-token-label">ACCESS TOKEN</span>
          <span className="atm-token-value">{token}</span>
        </div>

        <div className="atm-safety-banner">
          <ShieldIcon size={16} color="#7C3AED" />
          <p>
            <strong>Save this token somewhere safe.</strong>
            <br />
            You&rsquo;ll need it to return to your journey.
          </p>
        </div>

        {copyState === "error" && (
          <p className="atm-copy-error">
            The token could not be copied. Please copy it manually.
          </p>
        )}

        <div className="atm-actions-row">
          <button
            type="button"
            className={copyState === "copied" ? "atm-btn-outline" : "atm-btn-primary"}
            onClick={handleCopy}
          >
            {copyState === "copied" ? (
              <>
                <CheckIcon size={12} color="#7C3AED" /> Token copied
              </>
            ) : (
              "Copy Token"
            )}
          </button>
          <button
            type="button"
            className={copyState === "copied" ? "atm-btn-primary" : "atm-btn-outline"}
            onClick={onStartJourney}
          >
            Start My Journey
          </button>
        </div>
      </div>
    </div>
  );
}
