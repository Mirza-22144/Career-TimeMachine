import "../styles/AccessTokenRequired.css";
import TopNav from "../components/TopNav";
import { useAccessTokenFlow } from "../hooks/useAccessTokenFlow.js";

/**
 * AC 3.1.6: the dedicated page opened when a token-dependent nav item
 * (Choose Your Path, Practice Scenarios, Dashboard) is selected with no
 * active access token. Shares its access-token flow with <TopNav /> (same
 * pattern as LandingPage.jsx's Hero) - TopNav already owns rendering the
 * Generate/Access Token modals off that shared state, so this page only
 * needs to trigger them, not render its own copies.
 */
export default function AccessTokenRequired() {
  const flow = useAccessTokenFlow();

  return (
    <>
      <TopNav flow={flow} />
      <div className="atr-page">
        <div className="atr-card">
          <h1 className="atr-title">Access token required</h1>
          <p className="atr-message">
            Access token required. Generate or enter an access token to continue.
          </p>
          <button type="button" className="atr-cta" onClick={flow.openAccessModal}>
            Generate / Access Token
          </button>
        </div>
      </div>
    </>
  );
}
