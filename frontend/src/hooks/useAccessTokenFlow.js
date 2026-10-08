import { useState } from "react";
import { navigate } from "../navigate.js";
import { api } from "../api.js";
import { getActiveToken, hasActiveToken } from "../accessToken.js";
import { getResumeStep } from "../resumeStep.js";

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
  const [tokenCheckError, setTokenCheckError] = useState(false);
  // Last nav-gate attempt (and its options), so the "couldn't verify"
  // exception's Try Again button can re-run the exact same check instead
  // of just dismissing it.
  const [lastGateAction, setLastGateAction] = useState(null);
  const [lastGateOptions, setLastGateOptions] = useState(undefined);
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
  // its session, then takes her to the dashboard (AC 3.3.3) if her
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
      // AC 3.3.3: a returning visitor with a completed profile lands on
      // the dashboard.
      if (profile.confirmed) {
        navigate("/dashboard");
      } else {
        navigate(getResumeStep(profile));
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

  // Guards a token-dependent nav item (Choose Your Path, Practice
  // Scenarios, Dashboard). AC 3.1.6: with no active token, opens the
  // dedicated Access Token Required page instead of just blocking the
  // click. `requireProfile` (AC 3.3.3's rule, applied to every page that
  // depends on a career profile) additionally sends her back into the
  // wizard, at whichever step is actually unfinished, when a token exists
  // but the profile was never confirmed - same getResumeStep() used
  // everywhere else a confirmed profile is required.
  const attemptTokenGate = async (onAllowed, { requireProfile = false } = {}) => {
    try {
      setTokenCheckError(false);
      if (!hasActiveToken()) {
        navigate("/access-token-required");
        return;
      }
      if (requireProfile) {
        const profile = await api.getProfile();
        if (!profile.confirmed) {
          navigate(getResumeStep(profile));
          return;
        }
      }
      onAllowed();
    } catch {
      setTokenCheckError(true);
    }
  };
  const checkTokenGate = (onAllowed, options) => (e) => {
    e.preventDefault();
    setLastGateAction(() => onAllowed);
    setLastGateOptions(options);
    attemptTokenGate(onAllowed, options);
  };

  return {
    modalView,
    accessModalError,
    tokenGenerationError,
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
    lastGateOptions,
    lastValidToken,
  };
}
