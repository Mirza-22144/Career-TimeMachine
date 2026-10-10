import "../styles/LandingPage.css";
import { navigate } from "../navigate.js";
import heroBackground from "../assets/Background.png";
import heroVideo from "../assets/hero-background.mp4";
import {
  trustItems,
  statsSection,
  howItWorks,
  footerSection,
} from "../mockData/landingPageData";
import logoEmblem from "../assets/Logo.png";
import { ArrowRightIcon } from "../components/icons";
import TopNav from "../components/TopNav";
import { useAccessTokenFlow } from "../hooks/useAccessTokenFlow.js";
import { api } from "../api.js";
import { getResumeStep } from "../resumeStep.js";

/**
 * First screen visitors see, shown at the root URL "/" ("01 Landing"
 */

export default function LandingPage() {
  // Shared with <TopNav flow={flow} /> so the nav pill and this page's own
  // Hero CTA reflect the exact same access-token state - two independent
  // hook instances on one page would risk them drifting out of sync.
  const flow = useAccessTokenFlow();

  // "Continue your journey" (shown when a token is already active in this
  // tab). Career Journey requires a confirmed profile (409 otherwise) - a
  // token generated but never taken through the wizard has no confirmed
  // profile yet, so check first and resume at Your Story instead, same
  // rule already used for entering an existing token (handleValidToken).
  const handleContinueJourney = async () => {
    try {
      const profile = await api.getProfile();
      navigate(profile.confirmed ? "/dashboard" : getResumeStep(profile));
    } catch {
      navigate("/your-story");
    }
  };

  // The footer's links. The app's router owns the URL hash, so "How it
  // works" scrolls to its section here instead of using an #anchor (which
  // the router would read as a route and send her back to the top).
  const footerActions = {
    "how-it-works": () =>
      document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth" }),
    dashboard: flow.checkTokenGate(() => navigate("/dashboard"), { requireProfile: true }),
    start: flow.activeToken ? handleContinueJourney : flow.handleGenerateToken,
  };

  return (
    <div className="lp-page">
      <TopNav flow={flow} />

      {/* ---------- Hero ---------- */}
      <section className="lp-hero" id="hero" data-nav-dark>
        <div className="lp-hero-media">
          <video
            className="lp-hero-video"
            autoPlay
            muted
            loop
            playsInline
            poster={heroBackground}
            aria-hidden="true"
          >
            <source src={heroVideo} type="video/mp4" />
          </video>
          <div
            className="lp-hero-image lp-hero-image--fallback"
            style={{ backgroundImage: `url(${heroBackground})` }}
          />
        </div>
        <div className="lp-hero-scrim" />
        <div className="lp-hero-fade-bottom" />

        <div className="lp-hero-copy">
          <h1 className="lp-h1">You don&rsquo;t have to start over.</h1>
          <p className="lp-lead">Your experience is still valuable.</p>
          <p className="lp-brand-line">
            CareerTimeMachine helps women returning to IT reconnect with their
            experience, explore what&rsquo;s relevant today and practise
            their return with confidence.
          </p>

          {flow.activeToken ? (
            <div className="lp-active-journey">
              <span className="lp-active-journey-title">Your journey is saved.</span>
              <p className="lp-active-journey-text">
                Your access token is active. Continue where you left off.
              </p>
              <button
                type="button"
                className="lp-btn-primary"
                onClick={handleContinueJourney}
              >
                <span className="lp-btn-label">Continue your journey</span>
                <ArrowRightIcon size={16} />
              </button>
            </div>
          ) : (
            <div className="lp-active-journey">
              <span className="lp-active-journey-title">Ready to start your journey?</span>
              <p className="lp-active-journey-text">
                Generate an access token to save your journey and return to it later.
              </p>
              <button type="button" className="lp-btn-primary" onClick={flow.handleGenerateToken}>
                <span className="lp-btn-label">Generate Token</span>
              </button>
            </div>
          )}

          <div className="lp-trust-row">
            {trustItems.map((item) => (
              <div key={item} className="lp-trust-item">
                <span className="lp-trust-dot" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- Numbers ---------- */}
      <section className="lp-section lp-stats" id="stats">
        <h2 className="lp-h2">You are not alone in this.</h2>
        <p className="lp-lead lp-lead--section">{statsSection.intro}</p>

        <div className="lp-stat-grid">
          {statsSection.stats.map((stat) => (
            <div className="lp-stat-tile" key={stat.id}>
              <span className="lp-stat-value">{stat.value}</span>
              <span className="lp-stat-label">{stat.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ---------- How it works ---------- */}
      <section className="lp-section lp-how" id="how-it-works" aria-labelledby="how-it-works-heading">
        <span className="lp-how-eyebrow">HOW IT WORKS</span>
        <h2 className="lp-h2" id="how-it-works-heading">{howItWorks.heading}</h2>
        <p className="lp-lead lp-lead--section lp-how-intro">{howItWorks.intro}</p>

        <ol className="lp-how-steps">
          {howItWorks.steps.map((step, i) => (
            <li className="lp-how-step" key={step.id}>
              <div className="lp-how-marker" aria-hidden="true">
                <span className="lp-how-number">{i + 1}</span>
                {i < howItWorks.steps.length - 1 && <span className="lp-how-line" />}
              </div>
              <div className="lp-how-card">
                <span className="lp-how-stage">{step.stage}</span>
                <h3 className="lp-how-title">{step.title}</h3>
                <p className="lp-how-text">{step.text}</p>
                <span className="lp-how-result">
                  <span className="lp-visually-hidden">You leave with: </span>
                  {step.result}
                </span>
              </div>
            </li>
          ))}
        </ol>

        <div className="lp-how-closing">
          <p>{howItWorks.closing}</p>
          <button type="button" className="lp-btn-primary" onClick={footerActions.start}>
            <span className="lp-btn-label">{flow.activeToken ? "Continue your journey" : "Generate Token"}</span>
            <ArrowRightIcon size={16} />
          </button>
        </div>
      </section>

      {/* ---------- Footer ---------- */}
      <footer className="lp-footer" id="footer" data-nav-dark>
        <div className="lp-footer-top">
          <div className="lp-footer-brand">
            <div className="lp-logo">
              <span className="lp-logo-mark">
                <img
                  src={logoEmblem}
                  alt="CareerTimeMachine emblem"
                  className="lp-logo-emblem"
                />
              </span>
              {/* Wordmark rendered in white for contrast against the dark footer background. */}
              <span className="lp-logo-word lp-logo-word--dark">
                CareerTimeMachine
              </span>
            </div>
            <p className="lp-footer-tagline">{footerSection.tagline}</p>
          </div>

          <div className="lp-footer-columns">
            {footerSection.columns.map((column) => (
              <div key={column.heading} className="lp-footer-column">
                <span className="lp-footer-column-heading">
                  {column.heading}
                </span>
                <div className="lp-footer-links">
                  {column.links.map((link) => (
                    <button
                      key={link.id}
                      type="button"
                      className="lp-footer-link"
                      onClick={footerActions[link.id]}
                    >
                      {link.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="lp-footer-divider" />

        <div className="lp-footer-bottom">
          <span className="lp-footer-copyright">{footerSection.copyright}</span>
        </div>
      </footer>
    </div>
  );
}
