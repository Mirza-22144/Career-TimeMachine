import { useEffect, useState } from "react";
import "../styles/AccessTokenModal.css";
import { NOTICE_EVENT, consumeProfileIncomplete, hasProfileIncompleteNotice } from "../resumeStep.js";

/**
 * Shown on a profile step when she was sent back here because she tried to
 * open a page that needs a finished profile (Choose Your Path, practice,
 * the dashboard, her roadmap or Career Profile). Without it she lands back
 * on the wizard with no explanation. It appears once per redirect.
 */
export default function FinishProfileNotice() {
  const [isOpen, setIsOpen] = useState(() => hasProfileIncompleteNotice());

  // The note is cleared once this screen is showing, so it appears once.
  useEffect(() => {
    consumeProfileIncomplete();
  }, []);

  // She can also be sent "back" to the step she is already on, which does
  // not remount this screen.
  useEffect(() => {
    const onNotice = () => {
      if (consumeProfileIncomplete()) setIsOpen(true);
    };
    window.addEventListener(NOTICE_EVENT, onNotice);
    return () => window.removeEventListener(NOTICE_EVENT, onNotice);
  }, []);

  useEffect(() => {
    if (!isOpen) return undefined;
    const onKeyDown = (e) => {
      if (e.key === "Escape") setIsOpen(false);
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="atm-overlay" onClick={() => setIsOpen(false)}>
      <div
        className="atm-modal atm-modal--compact"
        role="dialog"
        aria-modal="true"
        aria-labelledby="fpn-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="atm-title" id="fpn-title">
          Finish setting up your profile first
        </h2>
        <p className="atm-subtitle">
          Your roadmap, practice and dashboard are built from your profile. Complete the steps here and save your
          profile, then those pages will open.
        </p>
        <div className="atm-actions-row">
          <button type="button" className="atm-btn-primary" onClick={() => setIsOpen(false)} autoFocus>
            Continue setting up
          </button>
        </div>
      </div>
    </div>
  );
}
