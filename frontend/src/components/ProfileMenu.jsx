import { useEffect, useRef, useState } from "react";
import "../styles/ProfileMenu.css";
import { UserIcon, ShieldIcon } from "./icons";
import { navigate } from "../navigate.js";

/**
 * Profile icon + dropdown shown in the nav once a token is active
 * (AC 3.1.7). Replaces the "My Token" pill - My Token moved into this
 * dropdown alongside Career Profile. Closes on an option select, an
 * outside click, or Escape; fully keyboard-operable (arrow-key free, but
 * Tab/Enter/Escape all work since every item is a real <button>).
 */
export default function ProfileMenu({ onViewToken }) {
  const [isOpen, setIsOpen] = useState(false);
  const rootRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;
    const onPointerDown = (e) => {
      if (rootRef.current && !rootRef.current.contains(e.target)) setIsOpen(false);
    };
    const onKeyDown = (e) => {
      if (e.key === "Escape") setIsOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [isOpen]);

  return (
    <div className="pm-root" ref={rootRef}>
      <button
        type="button"
        className="pm-trigger"
        aria-haspopup="menu"
        aria-expanded={isOpen}
        aria-label="Profile menu"
        onClick={() => setIsOpen((v) => !v)}
      >
        <UserIcon size={18} />
      </button>

      {isOpen && (
        <div className="pm-menu" role="menu">
          <button
            type="button"
            role="menuitem"
            className="pm-menu-item"
            onClick={() => {
              setIsOpen(false);
              onViewToken();
            }}
          >
            <span className="pm-menu-icon">
              <ShieldIcon size={16} />
            </span>
            <span className="pm-menu-text">
              <strong>My Token</strong>
              <span>See your token so you can come back later.</span>
            </span>
          </button>
          <button
            type="button"
            role="menuitem"
            className="pm-menu-item"
            onClick={() => {
              setIsOpen(false);
              navigate("/career-journey");
            }}
          >
            <span className="pm-menu-icon">
              <UserIcon size={16} />
            </span>
            <span className="pm-menu-text">
              <strong>Career Profile</strong>
              <span>Edit your details. Changes refresh your roadmap and suggestions.</span>
            </span>
          </button>
        </div>
      )}
    </div>
  );
}
