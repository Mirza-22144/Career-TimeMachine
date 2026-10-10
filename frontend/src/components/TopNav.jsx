import { useEffect, useRef, useState } from "react";
import "../styles/TopNav.css";
import { navigate, getCurrentPath } from "../navigate.js";
import logoEmblem from "../assets/Logo.png";
import { navLinks } from "../mockData/landingPageData.js";
import { useAccessTokenFlow } from "../hooks/useAccessTokenFlow.js";
import AccessTokenModal from "./AccessTokenModal";
import GeneratedTokenModal from "./GeneratedTokenModal";
import MyTokenModal from "./MyTokenModal";
import ProfileMenu from "./ProfileMenu";

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

  // The nav floats over the page: the logo is plain text and the links sit
  // on frosted glass, so each has to suit whatever is behind it. Pages mark
  // their dark areas (a hero photo, the wizard's sidebar, the landing
  // footer) with `data-nav-dark`; the logo and the links each turn white
  // while one of those is behind them, and stay dark otherwise.
  const logoRef = useRef(null);
  const actionsRef = useRef(null);
  const [onDark, setOnDark] = useState({ logo: false, actions: false });
  // The wordmark has no background of its own, so once the page has
  // scrolled and ordinary content is passing behind it, it steps aside and
  // leaves just the emblem.
  const [isScrolled, setIsScrolled] = useState(false);
  useEffect(() => {
    const isOverDark = (el) => {
      if (!el) return false;
      const box = el.getBoundingClientRect();
      const x = box.left + box.width / 2;
      const y = box.top + box.height / 2;
      return [...document.querySelectorAll("[data-nav-dark]")].some((area) => {
        const r = area.getBoundingClientRect();
        return r.width > 0 && x >= r.left && x <= r.right && y >= r.top && y <= r.bottom;
      });
    };
    const check = () => {
      const next = { logo: isOverDark(logoRef.current), actions: isOverDark(actionsRef.current) };
      setOnDark((now) => (now.logo === next.logo && now.actions === next.actions ? now : next));
      setIsScrolled(window.scrollY > 24);
    };
    check();
    window.addEventListener("scroll", check, { passive: true });
    window.addEventListener("resize", check);
    return () => {
      window.removeEventListener("scroll", check);
      window.removeEventListener("resize", check);
    };
    // No dependency list on purpose: a page can swap what is under the nav
    // without the route changing (the steps of the practice flow), and the
    // check only sets state when the answer changes.
  });

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
        <div
          className={`tn-logo ${onDark.logo ? "tn-on-dark" : ""} ${isScrolled && !onDark.logo ? "tn-logo--emblem-only" : ""}`}
          ref={logoRef}
        >
          <span className="tn-logo-mark">
            <img src={logoEmblem} alt="CareerTimeMachine emblem" className="tn-logo-emblem" />
          </span>
          <span className="tn-logo-word">CareerTimeMachine</span>
        </div>
        <div className={`tn-nav-actions ${onDark.actions ? "tn-on-dark" : ""}`} ref={actionsRef}>
          <div className="tn-nav-links">
            {navLinks.map((link) => {
              const isActive = link.href === currentPath;
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
                  onClick={flow.checkTokenGate(() => navigate(link.href), {
                    requireProfile: link.requireProfile,
                  })}
                >
                  {link.label}
                </button>
              );
            })}
          </div>
          {flow.activeToken ? (
            <ProfileMenu onViewToken={flow.handleViewToken} />
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

      {flow.tokenCheckError && (
        <div className="tn-modal-error">
          <span>We couldn&rsquo;t verify your access. Please try again.</span>
          <button
            type="button"
            onClick={() =>
              flow.lastGateAction && flow.attemptTokenGate(flow.lastGateAction, flow.lastGateOptions)
            }
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
