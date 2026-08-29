import { useRef, useState } from "react";
import "../styles/LandingPage.css";
import logoEmblem from "../assets/Logo.png";
import heroBackground from "../assets/Background.png";
import JourneyLine from "../components/JourneyLine";
import {
  navLinks,
  trustItems,
  heroWaypoints,
  experienceProfile,
  experienceSkills,
  pastSkills,
  newHorizons,
  defaultActiveSkillId,
  practiceScenario,
  adaptSection,
  reflectSection,
  eportfolioSection,
  closingSection,
  footerSection,
} from "../mockData/landingPageData";
import {
  ClockIcon,
  ArrowRightIcon,
  ArrowDownIcon,
  UserIcon,
  CloudIcon,
  CheckIcon,
  MessageCircleIcon,
  FileTextIcon,
  SpinnerIcon,
} from "../components/icons";

/**
 * Landing screen ("01 Landing", Figma node-id 11-93).
 *
 * Single-page flow: Navigation, Hero, and six content sections (Remember,
 * Discover, Practise, Adapt, Reflect, ePortfolio), ending in a Closing CTA
 * banner and Footer. A scroll-linked progress rail (JourneyLine) tracks
 * position through five of those sections.
 *
 * Interactivity policy: Discover is the only section a visitor can interact
 * with (hover a skill to see the future-skill areas it maps to). Every
 * other multi-option control (Practise's scenario options, Reflect's mood
 * selector) renders a fixed selection for demo purposes and does not
 * respond to clicks.
 */

// Center point of the "Your Experience" node in the Remember section's
// 1112x540 constellation canvas — used to draw the dashed lines from it to
// each floating skill pill.
const CENTER = { x: 324 + 66, y: 194 + 66 };

// Label shown on the nav/hero/closing CTAs. Returning-visitor detection
// (token-based "Continue" label) is out of scope until auth/tokens exist.
const journeyCtaLabel = "Enter My Journey";

export default function LandingPage() {
  const pageRef = useRef(null);

  // Which past-skill is highlighted in the Discover section; changes on
  // hover/focus (see the "Discover" section below).
  const [activeSkillId, setActiveSkillId] = useState(defaultActiveSkillId);
  const [ctaLoading, setCtaLoading] = useState(false);

  // Fixed demo selections for the Practise scenario and Reflect mood
  // selector — intentionally not backed by state, since neither responds
  // to user input (see mockData/landingPageData.js for the underlying data).
  const selectedOptionId = practiceScenario.defaultSelectedId;
  const selectedMoodId = reflectSection.defaultMoodId;
  const selectedOption = practiceScenario.options.find(
    (o) => o.id === selectedOptionId,
  );

  const activeSkill = pastSkills.find((s) => s.id === activeSkillId);
  const activeLeadsTo = activeSkill ? activeSkill.leadsTo : [];

  // Smooth-scrolls to an in-page section instead of following the anchor link.
  const scrollToId = (id) => (e) => {
    e.preventDefault();
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  // Shows a brief loading state on the CTA buttons before continuing.
  // Replace the timeout with real navigation once routing exists.
  const handleEnterJourney = () => {
    setCtaLoading(true);
    setTimeout(() => setCtaLoading(false), 1200);
  };

  return (
    <div className="lp-page" ref={pageRef}>
      <JourneyLine containerRef={pageRef} />

      {/* ---------- Navigation ---------- */}
      <nav className="lp-nav">
        <div className="lp-logo">
          <span className="lp-logo-mark">
            <img
              src={logoEmblem}
              alt="CareerTimeMachine emblem"
              className="lp-logo-emblem"
            />
          </span>
          <span className="lp-logo-word">CareerTimeMachine</span>
        </div>
        <div className="lp-nav-actions">
          <div className="lp-nav-links">
            {navLinks.map((link) =>
              link.clickable ? (
                <a
                  key={link.label}
                  href={link.href}
                  className="lp-nav-link"
                  onClick={scrollToId(link.href.replace("#", ""))}
                >
                  {link.label}
                </a>
              ) : (
                <span
                  key={link.label}
                  className="lp-nav-link lp-nav-link--static"
                  aria-disabled="true"
                >
                  {link.label}
                </span>
              ),
            )}
          </div>
          <button type="button" className="lp-btn-outline">
            {journeyCtaLabel}
          </button>
        </div>
      </nav>

      {/* ---------- Hero ---------- */}
      <section className="lp-hero" id="hero">
        <div className="lp-hero-copy">
          <div className="lp-eyebrow-pill">
            <ClockIcon size={11} />
            <span>CAREERTIMEMACHINE</span>
          </div>

          <h1 className="lp-h1">You don&rsquo;t have to start over.</h1>
          <p className="lp-lead">Your experience is still valuable.</p>
          <p className="lp-brand-line">
            CareerTimeMachine helps you understand where your experience fits
            today.
          </p>
          <p className="lp-supporting-copy">
            Explore new possibilities, practise realistic workplace
            situations and build confidence for your return to IT
          </p>
          <div className="lp-quote-row">
            <span className="lp-quote">
              Built around the real challenges of returning to IT.
            </span>
          </div>

          <div className="lp-ctas">
            <button
              type="button"
              className="lp-btn-primary"
              onClick={handleEnterJourney}
              disabled={ctaLoading}
            >
              <span
                className={
                  ctaLoading ? "lp-btn-label lp-btn-label--dim" : "lp-btn-label"
                }
              >
                {journeyCtaLabel}
              </span>
              {ctaLoading ? (
                <SpinnerIcon size={16} />
              ) : (
                <ArrowRightIcon size={16} />
              )}
            </button>
            <a
              href="#remember"
              className="lp-btn-ghost"
              onClick={scrollToId("remember")}
            >
              <span>See how it works</span>
              <ArrowDownIcon size={15} />
            </a>
          </div>

          <div className="lp-trust-row">
            {trustItems.map((item) => (
              <div key={item} className="lp-trust-item">
                <span className="lp-trust-dot" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="lp-hero-panel">
          <div
            className="lp-hero-image"
            style={{ backgroundImage: `url(${heroBackground})` }}
          />
          <div className="lp-hero-tint" />
          <div className="lp-hero-fade-left" />
          <div className="lp-hero-fade-bottom" />

          {/* Dashed line connecting the 4 hero waypoints, drawn through each
              waypoint's halo center (left+110, top+64 — constant across the
              active/inactive halo sizes). */}
          <svg className="lp-hero-journey-path" width="864" height="1024">
            <path
              d={`M ${heroWaypoints.map((wp) => `${wp.left + 110},${wp.top + 64}`).join(" L ")}`}
              fill="none"
              stroke="#A78BFA"
              strokeWidth="2"
              strokeDasharray="6 6"
            />
          </svg>

          {heroWaypoints.map((wp) => (
            <div
              key={wp.step}
              className={`lp-waypoint ${wp.active ? "lp-waypoint--active" : ""}`}
              style={{ left: wp.left, top: wp.top }}
            >
              <span className="lp-waypoint-halo" />
              <span className="lp-waypoint-core" />
              <span className="lp-waypoint-label">
                <span className="lp-waypoint-step">{wp.step}</span>
                <span className="lp-waypoint-name">{wp.label}</span>
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* ---------- Remember ---------- */}
      <section className="lp-section lp-remember" id="remember">
        <h2 className="lp-h2">Start with what you already know.</h2>
        <p className="lp-lead lp-lead--section">
          Your previous experience is the starting point.
        </p>

        <div className="lp-constellation">
          <svg className="lp-constellation-lines" width="1112" height="540">
            {experienceSkills.map((skill) => {
              const px = skill.left + 38;
              const py = skill.top + 21;
              return (
                <line
                  key={skill.id}
                  x1={CENTER.x}
                  y1={CENTER.y}
                  x2={px}
                  y2={py}
                  stroke="rgba(167, 139, 250, 0.28)"
                  strokeWidth="1.25"
                  strokeDasharray="4 4"
                />
              );
            })}
          </svg>

          <div className="lp-experience-core">
            <UserIcon size={24} />
            <span className="lp-experience-core-label">YOUR EXPERIENCE</span>
          </div>
          <div className="lp-profile-caption">
            <span className="lp-profile-role">{experienceProfile.role}</span>
            <span className="lp-profile-tenure">
              {experienceProfile.tenure}
            </span>
          </div>

          {/* Fixed demo state: the skill with a contextLabel (Java) renders
              permanently active; no hover interactivity in this section. */}
          {experienceSkills.map((skill) => {
            const isActive = !!skill.contextLabel;
            return (
              <div
                key={skill.id}
                className="lp-skill-pill-wrap"
                style={{ left: skill.left, top: skill.top }}
              >
                {isActive && (
                  <span className="lp-skill-context">{skill.contextLabel}</span>
                )}
                <span
                  className={`lp-skill-pill ${isActive ? "lp-skill-pill--active" : ""}`}
                >
                  <span className="lp-skill-dot" />
                  {skill.name}
                </span>
              </div>
            );
          })}
        </div>
      </section>

      {/* ---------- Discover ---------- */}
      <section className="lp-section lp-discover" id="discover">
        <h2 className="lp-h2">See what is relevant today.</h2>
        <p className="lp-lead lp-lead--section">
          Recognise what you already bring and explore current in-demand skills.
        </p>
        <div className="lp-hint-pill">
          <span className="lp-trust-dot" />
          <span>Hover a skill to trace where it leads</span>
        </div>

        <div className="lp-translation-map">
          <span className="lp-map-column-label lp-map-column-label--left">
            YOUR EXPERIENCE
          </span>
          <span className="lp-map-column-label lp-map-column-label--right">
            NEW HORIZONS
          </span>

          <svg className="lp-map-lines" width="1112" height="400">
            {pastSkills.map((skill, i) =>
              newHorizons.map((horizon, j) => {
                const isActive =
                  skill.id === activeSkillId &&
                  skill.leadsTo.includes(horizon.id);
                if (!isActive) return null;
                const y1 = 44 + i * 82 + 31;
                const y2 = 44 + j * 82 + 31;
                return (
                  <path
                    key={`${skill.id}-${horizon.id}`}
                    d={`M268,${y1} C556,${y1} 556,${y2} 844,${y2}`}
                    fill="none"
                    stroke="#8B5CF6"
                    strokeWidth="2"
                  />
                );
              }),
            )}
          </svg>

          <div className="lp-map-column lp-map-column--left">
            {pastSkills.map((skill) => {
              const isActive = skill.id === activeSkillId;
              return (
                <button
                  type="button"
                  key={skill.id}
                  className={`lp-map-card lp-map-card--skill ${isActive ? "lp-map-card--active" : "lp-map-card--dim"}`}
                  onMouseEnter={() => setActiveSkillId(skill.id)}
                  onFocus={() => setActiveSkillId(skill.id)}
                >
                  <span className="lp-skill-dot lp-skill-dot--map" />
                  {skill.name}
                </button>
              );
            })}
          </div>

          <div className="lp-map-column lp-map-column--right">
            {newHorizons.map((horizon) => {
              const isActive = activeLeadsTo.includes(horizon.id);
              return (
                <div
                  key={horizon.id}
                  className={`lp-map-card lp-map-card--horizon ${isActive ? "lp-map-card--active" : "lp-map-card--dim"}`}
                >
                  <span className="lp-map-icon-box">
                    <CloudIcon size={17} />
                  </span>
                  <span className="lp-map-horizon-text">
                    <span className="lp-map-horizon-name">{horizon.name}</span>
                    <span className="lp-map-horizon-desc">
                      {horizon.description}
                    </span>
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ---------- Practise ---------- */}
      <section className="lp-section lp-practise" id="practise">
        <h2 className="lp-h2">Try it before you return.</h2>
        <p className="lp-lead lp-lead--section">
          A real workplace situation, at your own pace.
        </p>

        <div className="lp-practice-window">
          <div className="lp-practice-titlebar">
            <div className="lp-practice-dots">
              <span className="lp-dot lp-dot--1" />
              <span className="lp-dot lp-dot--2" />
              <span className="lp-dot lp-dot--3" />
            </div>
            <div className="lp-practice-url">{practiceScenario.url}</div>
          </div>

          <div className="lp-scenario">
            <div className="lp-scenario-question">
              <span className="lp-scenario-label">
                {practiceScenario.scenarioLabel}
              </span>
              <h3 className="lp-scenario-heading">
                {practiceScenario.question}
              </h3>

              {/* Fixed demo state: "Check logs" renders selected; the other
                  options display for visual completeness but aren't
                  clickable. */}
              <div className="lp-scenario-options">
                {practiceScenario.options.map((option) => {
                  const isSelected = option.id === selectedOptionId;
                  return (
                    <div
                      key={option.id}
                      className={`lp-option ${isSelected ? "lp-option--selected" : ""} ${!isSelected ? "lp-option--static" : ""}`}
                      aria-disabled={!isSelected}
                    >
                      <span className="lp-option-radio">
                        {isSelected && <CheckIcon size={10} />}
                      </span>
                      <span className="lp-option-label">{option.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="lp-scenario-feedback">
              <div className="lp-feedback-card">
                <div className="lp-feedback-header">
                  <span className="lp-feedback-icon">
                    <CheckIcon size={13} />
                  </span>
                  <span className="lp-feedback-heading">
                    {selectedOption.feedback.heading}
                  </span>
                </div>
                <p className="lp-feedback-main">{selectedOption.feedback.main}</p>
                <p className="lp-feedback-note">
                  {selectedOption.feedback.note}
                </p>
              </div>

              <div className="lp-scenario-stages">
                {practiceScenario.stages.map((stage, i) => (
                  <span key={stage} className="lp-stage-group">
                    {i > 0 && <span className="lp-stage-dot" />}
                    <span
                      className={`lp-stage ${stage === practiceScenario.activeStage ? "lp-stage--active" : ""}`}
                    >
                      {stage}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------- Adapt ---------- */}
      <section className="lp-section lp-adapt" id="adapt">
        <h2 className="lp-h2">{adaptSection.heading}</h2>
        <p className="lp-lead lp-lead--section">{adaptSection.subheading}</p>

        <div className="lp-loop">
          <span className="lp-loop-ring lp-loop-ring--outer" />
          <span className="lp-loop-ring lp-loop-ring--inner" />

          {adaptSection.loopArrows.map((arrow, i) => (
            <span
              key={i}
              className="lp-loop-arrow"
              style={{
                left: arrow.x,
                top: arrow.y,
                transform: `translate(-50%, -50%) rotate(${arrow.rotation}deg)`,
              }}
            />
          ))}

          <div className="lp-loop-prompt">
            <span className="lp-loop-prompt-icon">
              <MessageCircleIcon size={17} />
            </span>
            <p className="lp-loop-prompt-text">
              {adaptSection.adaptivePromptText}
            </p>
          </div>

          {adaptSection.loopNodes.map((node) => (
            <div
              key={node.id}
              className="lp-loop-node"
              style={{ left: node.left, top: node.top }}
            >
              <span className="lp-loop-node-dot" />
              <span className="lp-loop-node-label">{node.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ---------- Reflect ---------- */}
      <section className="lp-section lp-reflect" id="reflect">
        <h2 className="lp-h2">{reflectSection.heading}</h2>
        <p className="lp-lead lp-lead--section">{reflectSection.subheading}</p>

        <div className="lp-confidence-path">
          <svg className="lp-confidence-svg" width="1112" height="280">
            <path
              d={`M ${reflectSection.confidenceCurve.points.map((p) => `${p.x},${p.y}`).join(" L ")}`}
              fill="none"
              stroke="rgba(124, 58, 237, 0.25)"
              strokeWidth="2"
            />
            {reflectSection.confidenceCurve.points.map((p, i) => (
              <circle
                key={i}
                cx={p.x}
                cy={p.y}
                r={p.r}
                fill="#7C3AED"
                fillOpacity={p.opacity}
                stroke="#FFFFFF"
                strokeWidth="2.5"
                style={
                  p.glow
                    ? {
                        filter: "drop-shadow(0 0 14px rgba(139, 92, 246, 0.6))",
                      }
                    : undefined
                }
              />
            ))}
          </svg>
          <span
            className="lp-confidence-label lp-confidence-label--start"
            style={{
              left: reflectSection.confidenceCurve.startLabel.left,
              top: reflectSection.confidenceCurve.startLabel.top,
            }}
          >
            {reflectSection.confidenceCurve.startLabel.text}
          </span>
          <span
            className="lp-confidence-label lp-confidence-label--ready"
            style={{
              left: reflectSection.confidenceCurve.readyLabel.left,
              top: reflectSection.confidenceCurve.readyLabel.top,
            }}
          >
            {reflectSection.confidenceCurve.readyLabel.text}
          </span>
        </div>

        <h3 className="lp-reflect-question">{reflectSection.question}</h3>

        {/* Fixed demo state: the default mood renders selected; the other
            pills display for visual completeness but aren't clickable. */}
        <div className="lp-mood-row">
          {reflectSection.moods.map((mood) => {
            const isActive = mood.id === selectedMoodId;
            return (
              <div
                key={mood.id}
                className={`lp-mood-pill ${isActive ? "lp-mood-pill--active" : ""} ${!isActive ? "lp-mood-pill--static" : ""}`}
                aria-disabled={!isActive}
              >
                <span className="lp-mood-dot" />
                {mood.label}
              </div>
            );
          })}
        </div>

        <div className="lp-next-intent">
          <span className="lp-next-intent-icon">
            <CheckIcon size={12} color="#7C3AED" />
          </span>
          <span className="lp-next-intent-text">
            {reflectSection.nextIntentText}
          </span>
        </div>
      </section>

      {/* ---------- ePortfolio ---------- */}
      <section className="lp-section lp-eportfolio" id="eportfolio">
        <h2 className="lp-h2 lp-h2--wide">{eportfolioSection.heading}</h2>

        <div className="lp-portfolio-layout">
          <div className="lp-portfolio-stack">
            <div className="lp-portfolio-ghost lp-portfolio-ghost--1" />
            <div className="lp-portfolio-ghost lp-portfolio-ghost--2" />

            <div className="lp-portfolio-preview">
              <div className="lp-portfolio-header">
                <span className="lp-portfolio-avatar">
                  <UserIcon size={21} color="#FFFFFF" />
                </span>
                <div className="lp-portfolio-titles">
                  <span className="lp-portfolio-title">
                    {eportfolioSection.preview.title}
                  </span>
                  <span className="lp-portfolio-subtitle">
                    {eportfolioSection.preview.subtitle}
                  </span>
                </div>
                <span className="lp-portfolio-badge">
                  {eportfolioSection.preview.badge}
                </span>
              </div>

              <div className="lp-portfolio-divider" />

              <div className="lp-portfolio-sections">
                {eportfolioSection.preview.sections.map((section) => (
                  <div
                    key={section.id}
                    className={`lp-portfolio-row ${section.active ? "lp-portfolio-row--active" : ""}`}
                  >
                    <span className="lp-portfolio-row-icon">
                      <FileTextIcon size={15} />
                    </span>
                    <span className="lp-portfolio-row-text">
                      <span className="lp-portfolio-row-title">
                        {section.title}
                      </span>
                      <span className="lp-portfolio-row-desc">
                        {section.description}
                      </span>
                    </span>
                    <span className="lp-portfolio-row-check">
                      <CheckIcon size={11} color="#7C3AED" />
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="lp-portfolio-caption">
            <span className="lp-portfolio-caption-eyebrow">
              {eportfolioSection.captionEyebrow}
            </span>
            <p className="lp-portfolio-caption-text">
              {eportfolioSection.captionText}
            </p>
          </div>
        </div>
      </section>

      {/* ---------- Closing ---------- */}
      <section className="lp-closing" id="closing">
        <div
          className="lp-closing-image"
          style={{ backgroundImage: `url(${heroBackground})` }}
        />
        <div className="lp-closing-scrim" />

        <div className="lp-closing-copy">
          <p className="lp-closing-line-before">{closingSection.lineBefore}</p>
          <div className="lp-closing-transition">
            <span className="lp-closing-transition-bar" />
            <span className="lp-closing-transition-marker" />
          </div>
          <p className="lp-closing-line-after">{closingSection.lineAfter}</p>
          <p className="lp-closing-subtext">{closingSection.subtext}</p>
          <button
            type="button"
            className="lp-btn-primary lp-closing-cta"
            onClick={handleEnterJourney}
            disabled={ctaLoading}
          >
            <span
              className={
                ctaLoading ? "lp-btn-label lp-btn-label--dim" : "lp-btn-label"
              }
            >
              {journeyCtaLabel}
            </span>
            {ctaLoading ? (
              <SpinnerIcon size={16} />
            ) : (
              <ArrowRightIcon size={16} />
            )}
          </button>
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
                  {column.links.map((link) => (
                    <a key={link} href="#" className="lp-footer-link">
                      {link}
                    </a>
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
