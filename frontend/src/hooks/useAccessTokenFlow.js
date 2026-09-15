import { useState } from "react";
import { navigate } from "../navigate.js";
import { api } from "../api.js";
import { getActiveToken, hasActiveToken, setJustReturned } from "../accessToken.js";

/**
 * All the access-token/modal state shared by TopNav (every page) and the
 * Landing page's own Hero CTA. Kept as one hook so a single call site (see
 * LandingPage.jsx, the only page whose own content also needs this state)
 * can share one instance with <TopNav flow={flow} /> instead of the nav
 * pill and the Hero drifting out of sync with two separate instances.
 */
export function useAccessTokenFlow() {
  // Which modal is showing: null (none), "options" (AC 3.1.1), "token"
  // (AC 3.1.2, just generated) or "my-token" (AC 3.1.5, viewing an
  // already-active token).
  const [modalView, setModalView] = useState(null);
  const [accessModalError, setAccessModalError] = useState(false);
  const [tokenGenerationError, setTokenGenerationError] = useState(false);
  const [isTokenRequiredOpen, setIsTokenRequiredOpen] = useState(false);
  const [tokenCheckError, setTokenCheckError] = useState(false);
  // Last nav-gate attempt, so the "couldn't verify" exception's Try Again
  // button can re-run the same check instead of just dismissing it.
  const [lastGateAction, setLastGateAction] = useState(null);
  // Mirrors accessToken.js in local state (AC 3.1.5) so the nav pill and
  // Hero CTA re-render as soon as a token is generated or entered, instead
  // of only reflecting it after the next full page load.
  const [activeToken, setActiveTokenState] = useState(() => getActiveToken());
  const [loadTokenError, setLoadTokenError] = useState(false);
  // AC 3.2.1: restoring/creating the session behind an entered token.
  const [sessionRestoreError, setSessionRestoreError] = useState(false);
  const [lastValidToken, setLastValidToken] = useState(null);

  const closeModal = () => setModalView(null);

  // Opens the "Access Your Journey" modal (AC 3.1.1). Runs when the user
  // selects Enter My Journey on the Hero or Generate/Access Token in the
  // nav - both lead to the same modal.
  const openAccessModal = () => {
    try {
      setAccessModalError(false);
      setModalView("options");
    } catch {
      setAccessModalError(true);
    }
  };

  // Generates a new real access token and moves to the token-display modal
  // (AC 3.1.2). `force: true` always mints a brand-new token, even if one is
  // already stored - Generate Token is a deliberate "start a new journey"
  // action. Not reachable while a token is already active (AC 3.1.5) - the
  // nav only offers Generate/Access Token before that point.
  const handleGenerateToken = async () => {
    try {
      const token = await api.createSession(true);
      setActiveTokenState(token);
      setTokenGenerationError(false);
      setModalView("token");
    } catch {
      setTokenGenerationError(true);
    }
  };

  // AC 3.2.1: validates an entered token against the real backend, restores
  // its session, then takes her to Career Journey ("welcome back") if her
  // profile is already confirmed, or back into the wizard at Your Story if
  // she never finished it. `silent: true` (used by AccessTokenModal) skips
  // the sessionRestoreError toast so the modal can show its own inline
  // message instead, without a second network round-trip - the toast's own
  // "Try Again" retry (no modal open) still uses the default, non-silent
  // path. Returns 'ok' | 'invalid' | 'network' so callers can react without
  // re-checking anything themselves.
  const handleValidToken = async (token, { silent = false } = {}) => {
    setLastValidToken(token);
    let isValid;
    try {
      isValid = await api.validateToken(token);
    } catch {
      if (!silent) setSessionRestoreError(true);
      return "network";
    }
    if (!isValid) {
      if (!silent) setSessionRestoreError(true);
      return "invalid";
    }
    try {
      api.restoreSession(token);
      const profile = await api.getProfile();
      setSessionRestoreError(false);
      setActiveTokenState(token);
      if (profile.confirmed) {
        setJustReturned();
        navigate("/career-journey");
      } else {
        navigate("/your-story");
      }
      return "ok";
    } catch {
      if (!silent) setSessionRestoreError(true);
      return "network";
    }
  };

  // Opens the "My Token" view (AC 3.1.5) for a visitor who already has an
  // active token. Reads it fresh rather than trusting local state, so a
  // genuine retrieval failure can actually be caught and shown. Copy-only -
  // see MyTokenModal for why this must never offer a way into Your Story.
  const handleViewToken = () => {
    try {
      const token = getActiveToken();
      if (!token) throw new Error("no active token");
      setLoadTokenError(false);
      setModalView("my-token");
    } catch {
      setLoadTokenError(true);
    }
  };

  // Guards a token-dependent nav item (Career Journey, Practice Scenarios,
  // ePortfolio). Shows the "access token required" notice when there is no
  // active token yet; runs `onAllowed` when there is one.
  const attemptTokenGate = (onAllowed) => {
    try {
      setTokenCheckError(false);
      if (hasActiveToken()) {
        onAllowed();
      } else {
        setIsTokenRequiredOpen(true);
      }
    } catch {
      setTokenCheckError(true);
    }
  };
  const checkTokenGate = (onAllowed) => (e) => {
    e.preventDefault();
    setLastGateAction(() => onAllowed);
    attemptTokenGate(onAllowed);
  };

  return {
    modalView,
    accessModalError,
    tokenGenerationError,
    isTokenRequiredOpen,
    setIsTokenRequiredOpen,
    tokenCheckError,
    activeToken,
    loadTokenError,
    sessionRestoreError,
    closeModal,
    openAccessModal,
    handleGenerateToken,
    handleValidToken,
    handleViewToken,
    checkTokenGate,
    attemptTokenGate,
    lastGateAction,
    lastValidToken,
  };
}
