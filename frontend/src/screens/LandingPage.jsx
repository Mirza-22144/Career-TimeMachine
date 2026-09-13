import "../styles/LandingPage.css";
import { navigate } from "../navigate.js";
import heroBackground from "../assets/Background.png";
import heroVideo from "../assets/hero-background.mp4";
import {
  trustItems,
  statsSection,
  roadmapSteps,
  footerSection,
} from "../mockData/landingPageData";
import logoEmblem from "../assets/Logo.png";
import { ArrowRightIcon, ArrowDownIcon } from "../components/icons";
import TopNav from "../components/TopNav";
import { useAccessTokenFlow } from "../hooks/useAccessTokenFlow.js";

/**
 * First screen visitors see, shown at the root URL "/" ("01 Landing"
 */

// Label shown on the Hero CTA. Returning-visitor detection (token-based
// "Continue" label) is out of scope until auth/tokens exist.
const journeyCtaLabel = "Enter My Journey";

export default function LandingPage() {
  // Shared with <TopNav flow={flow} /> so the nav pill and this page's own
  // Hero CTA reflect the exact same access-token state - two independent
  // hook instances on one page would risk them drifting out of sync.
  const flow = useAccessTokenFlow();

  // Smooth-scrolls to an in-page section instead of following the anchor link.
  const scrollToId = (id) => (e) => {
    e.preventDefault();
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="lp-page">
      <TopNav flow={flow} />

      {/* ---------- Hero ---------- */}
      <section className="lp-hero" id="hero">
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
                onClick={() => navigate("/career-journey")}
              >
                <span className="lp-btn-label">Continue your journey</span>
                <ArrowRightIcon size={16} />
              </button>
            </div>
          ) : (
            <div className="lp-ctas">
              <button
                type="button"
                className="lp-btn-primary"
                onClick={flow.openAccessModal}
              >
                <span className="lp-btn-label">{journeyCtaLabel}</span>
                <ArrowRightIcon size={16} />
              </button>
              <a
                href="#roadmap"
                className="lp-btn-ghost"
                onClick={scrollToId("roadmap")}
              >
                <span>See how it works</span>
                <ArrowDownIcon size={15} />
              </a>
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

      {/* ---------- Roadmap ---------- */}
      <section className="lp-section lp-roadmap" id="roadmap">
        <h2 className="lp-h2">Your journey, step by step.</h2>
        <p className="lp-lead lp-lead--section">
          From remembering what you know to moving forward with confidence.
        </p>

        <div className="lp-roadmap-steps">
          {roadmapSteps.map((step, i) => (
            <div className="lp-roadmap-step" key={step.id}>
              <span className="lp-roadmap-step-badge">{step.step}</span>
              <span className="lp-roadmap-step-title">{step.title}</span>
              <p className="lp-roadmap-step-caption">{step.caption}</p>
              {i < roadmapSteps.length - 1 && (
                <span className="lp-roadmap-connector" aria-hidden="true" />
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ---------- Footer ---------- */}
      <footer className="lp-footer" id="footer">
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
                  {column.links.map((link) => {
                    // "Practice scenarios" and "Your ePortfolio" aren't built
                    // for this iteration yet - shown, but visually inert.
                    const isStatic =
                      link === "Practice scenarios" || link === "Your ePortfolio";
                    return (
                      <a
                        key={link}
                        href="#"
                        className={`lp-footer-link ${isStatic ? "lp-footer-link--static" : ""}`}
                        aria-disabled={isStatic || undefined}
                      >
                        {link}
                      </a>
                    );
                  })}
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
