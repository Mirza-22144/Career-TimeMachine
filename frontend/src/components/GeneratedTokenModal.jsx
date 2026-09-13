import { useState } from "react";
import "../styles/AccessTokenModal.css";
import { ShieldIcon, CheckIcon } from "./icons";

// Selects and copies text via the older execCommand approach. Used when
// navigator.clipboard is unavailable or blocked (e.g. no clipboard-write
// permission, an insecure context, or an older browser) - the modern API
// alone can silently fail in exactly those cases with no fallback.
function copyWithFallback(text) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  textarea.setSelectionRange(0, text.length);
  const succeeded = document.execCommand("copy");
  document.body.removeChild(textarea);
  if (!succeeded) throw new Error("execCommand copy failed");
}

/**
 * "Your access token" modal (AC 3.1.2). Shown after Generate Token succeeds
 * on the Access Your Journey modal. Copy Token tries the modern Clipboard
 * API first, falls back to the older execCommand approach if that is
 * unavailable or fails, and only then shows the manual-copy error; Start My
 * Journey moves on to the wizard's first step.
 */
export default function GeneratedTokenModal({ token, onClose, onStartJourney }) {
  const [copyState, setCopyState] = useState("idle"); // idle | copied | error

  const handleCopy = async () => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(token);
      } else {
        copyWithFallback(token);
      }
      setCopyState("copied");
    } catch {
      try {
        copyWithFallback(token);
        setCopyState("copied");
      } catch {
        setCopyState("error");
      }
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
