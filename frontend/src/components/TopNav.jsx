import "../styles/TopNav.css";
import { navigate, getCurrentPath } from "../navigate.js";
import logoEmblem from "../assets/Logo.png";
import { navLinks } from "../mockData/landingPageData.js";
import { useAccessTokenFlow } from "../hooks/useAccessTokenFlow.js";
import AccessTokenModal from "./AccessTokenModal";
import GeneratedTokenModal from "./GeneratedTokenModal";
import MyTokenModal from "./MyTokenModal";
import TokenRequiredModal from "./TokenRequiredModal";

// Every wizard step belongs conceptually under Career Journey (its Edit
// buttons route back into these exact same steps), so the nav should show
// Career Journey as active while inside any of them too, not just on the
// literal "/career-journey" URL.
const WIZARD_PATHS = ["/your-story", "/your-experience", "/your-break", "/skill-relevance-map", "/your-direction"];

/**
 * Fixed top nav shared by every page (Landing, the onboarding wizard,
 * Career Journey, Workplace Scenario). Owns the access-token modals and
 * their exception banners, so any page that renders <TopNav /> gets the
 * full Generate/Access Token flow for free.
 *
 * Pages whose own content also needs this state (currently only
 * LandingPage.jsx, for its Hero CTA) should call useAccessTokenFlow()
 * themselves and pass the result as `flow`, so the nav pill and that page's
 * own UI share one instance instead of drifting out of sync.
 */
export default function TopNav({ flow: providedFlow }) {
  const ownFlow = useAccessTokenFlow();
  const flow = providedFlow || ownFlow;
  const currentPath = getCurrentPath();

  const handleHomeClick = (e) => {
    e.preventDefault();
    if (currentPath === "/") {
      document.getElementById("hero")?.scrollIntoView({ behavior: "smooth" });
    } else {
      navigate("/");
    }
  };

  return (
    <>
      <nav className="tn-nav">
        <div className="tn-logo">
          <span className="tn-logo-mark">
            <img src={logoEmblem} alt="CareerTimeMachine emblem" className="tn-logo-emblem" />
          </span>
          <span className="tn-logo-word">CareerTimeMachine</span>
        </div>
        <div className="tn-nav-actions">
          <div className="tn-nav-links">
            {navLinks.map((link) => {
              const isActive = link.href === currentPath
                || (link.href === "/career-journey" && WIZARD_PATHS.includes(currentPath));
              if (!link.gated) {
                // "Home" is the only ungated link today - path-aware since
                // it now renders on every page, not just Landing.
                return (
                  <a
                    key={link.label}
                    href={link.href}
                    className={`tn-nav-link ${isActive ? "tn-nav-link--active" : ""}`}
                    onClick={handleHomeClick}
                  >
                    {link.label}
                  </a>
                );
              }
              return (
                <button
                  key={link.label}
                  type="button"
                  className={`tn-nav-link tn-nav-link--button ${isActive ? "tn-nav-link--active" : ""}`}
                  onClick={flow.checkTokenGate(() => {
                    // ePortfolio has no real page yet - everything else
                    // (Career Journey, Practice Scenarios) does.
                    if (!link.href.startsWith("#")) navigate(link.href);
                  })}
                >
                  {link.label}
                </button>
              );
            })}
          </div>
          {flow.activeToken ? (
            <button type="button" className="tn-token-pill" onClick={flow.handleViewToken}>
              <span className="tn-token-pill-dot" />
              My Token
            </button>
          ) : (
            <button type="button" className="tn-token-pill" onClick={flow.openAccessModal}>
              <span className="tn-token-pill-dot" />
              Generate / Access Token
            </button>
          )}
        </div>
      </nav>

      {flow.modalView === "options" && (
        <AccessTokenModal
          onClose={flow.closeModal}
          onGenerateToken={flow.handleGenerateToken}
          onValidToken={flow.handleValidToken}
        />
      )}

      {flow.modalView === "token" && (
        <GeneratedTokenModal
          token={flow.activeToken}
          onClose={flow.closeModal}
          onStartJourney={() => navigate("/your-story")}
        />
      )}

      {flow.modalView === "my-token" && (
        <MyTokenModal token={flow.activeToken} onClose={flow.closeModal} />
      )}

      {flow.accessModalError && (
        <div className="tn-modal-error">
          <span>We couldn&rsquo;t open access options. Please try again.</span>
          <button type="button" onClick={flow.openAccessModal}>
            Try Again
          </button>
        </div>
      )}

      {flow.tokenGenerationError && (
        <div className="tn-modal-error">
          <span>We couldn&rsquo;t generate your access token. Please try again.</span>
          <button type="button" onClick={flow.handleGenerateToken}>
            Try Again
          </button>
        </div>
      )}

      {flow.isTokenRequiredOpen && (
        <TokenRequiredModal onClose={() => flow.setIsTokenRequiredOpen(false)} />
      )}

      {flow.tokenCheckError && (
        <div className="tn-modal-error">
          <span>We couldn&rsquo;t verify your access. Please try again.</span>
          <button
            type="button"
            onClick={() => flow.lastGateAction && flow.attemptTokenGate(flow.lastGateAction)}
          >
            Try Again
          </button>
        </div>
      )}

      {flow.loadTokenError && (
        <div className="tn-modal-error">
          <span>We couldn&rsquo;t load your access token. Please try again.</span>
          <button type="button" onClick={flow.handleViewToken}>
            Try Again
          </button>
        </div>
      )}

      {flow.sessionRestoreError && (
        <div className="tn-modal-error">
          <span>We couldn&rsquo;t load your saved journey. Please try again.</span>
          <button
            type="button"
            onClick={() => flow.lastValidToken && flow.handleValidToken(flow.lastValidToken)}
          >
            Try Again
          </button>
        </div>
      )}
    </>
  );
}
