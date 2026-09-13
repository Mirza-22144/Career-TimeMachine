import { useState } from "react";
import { navigate } from "../navigate.js";
import { api } from "../api.js";
import {
  getActiveToken,
  hasActiveToken,
  setActiveToken,
  recordTokenSession,
  getSessionForToken,
  setJustReturned,
} from "../accessToken.js";

// Chars exclude visually-ambiguous ones (0/O, 1/I, etc). Placeholder client-
// side generator until BE 3.x wires up a real backend-issued token.
const TOKEN_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
function generateMockToken() {
  const segment = () =>
    Array.from({ length: 4 }, () => TOKEN_CHARS[Math.floor(Math.random() * TOKEN_CHARS.length)]).join("");
  return `CTM-${segment()}-${segment()}`;
}

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

  // Generates a new token, starts a real session for it, and moves to the
  // token-display modal (AC 3.1.2). The token itself is still a client-side
  // mock, but the session behind it is real - swap the mock generator for a
  // real backend call once BE 3.x exists, keeping this same try/catch shape
  // for the failure case. Not reachable while a token is already active
  // (AC 3.1.5) - the nav only offers Generate/Access Token before that point.
  const handleGenerateToken = async () => {
    try {
      const token = generateMockToken();
      const sessionToken = await api.createSession();
      recordTokenSession(token, sessionToken);
      setActiveToken(token);
      setActiveTokenState(token);
      setTokenGenerationError(false);
      setModalView("token");
    } catch {
      setTokenGenerationError(true);
    }
  };

  // AC 3.2.1: restores the session behind a validated existing token (or
  // starts a fresh one if this token has no known mapping yet - e.g. it was
  // generated on a different browser, or local storage was cleared; that's
  // an absent mock mapping, not a real save failure, so it isn't treated as
  // one), then takes her to a "welcome back" Career Journey.
  const handleValidToken = async (token) => {
    setLastValidToken(token);
    try {
      const mappedSession = getSessionForToken(token);
      if (mappedSession) {
        api.restoreSession(mappedSession);
      } else {
        recordTokenSession(token, await api.createSession());
      }
      setSessionRestoreError(false);
      setActiveTokenState(token);
      setJustReturned();
      navigate("/career-journey");
    } catch {
      setSessionRestoreError(true);
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
