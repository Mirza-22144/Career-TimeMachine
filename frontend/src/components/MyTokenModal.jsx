import { useState } from "react";
import "../styles/AccessTokenModal.css";
import { CheckIcon } from "./icons";
import { copyToClipboard } from "../copyToClipboard.js";

/**
 * "My Access Token" modal (AC 3.1.5). Shown when a visitor with an active
 * token selects My Token in the nav. Copy-only, on purpose - there is no
 * Start My Journey button here, so this can never be used as a second
 * entry point into Your Story. The only real entry points are the Hero's
 * Continue your journey button and the flow right after a token is first
 * generated or entered (GeneratedTokenModal).
 */
export default function MyTokenModal({ token, onClose }) {
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
        className="atm-modal atm-modal--compact"
        role="dialog"
        aria-modal="true"
        aria-labelledby="mtm-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="atm-header">
          <h2 className="atm-title" id="mtm-title">
            My Access Token
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
          The token for your active journey. Keep it somewhere safe.
        </p>

        <div className="atm-token-box">
          <span className="atm-token-label">ACCESS TOKEN</span>
          <span className="atm-token-value">{token}</span>
        </div>

        {copyState === "error" && (
          <p className="atm-copy-error">
            The token could not be copied. Please copy it manually.
          </p>
        )}

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
      </div>
    </div>
  );
}
