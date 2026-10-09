import { useState } from "react";
import "../styles/AnalyseJobDescription.css";
import TopNav from "../components/TopNav";
import LoadingPopup from "../components/LoadingPopup";
import { api, ApiError } from "../api.js";
import { navigate } from "../navigate.js";
import { setCurrentJobDescriptionId } from "../currentJob.js";

const MIN_CHARACTERS = 150;
const MAX_CHARACTERS = 20000;

const howThisWorks = [
  {
    title: "Paste the whole ad",
    text: "Responsibilities and requirements matter more than the job title.",
  },
  {
    title: "We tidy it first",
    text: "Formatting and any code are removed before it is analysed.",
  },
  {
    title: "Then you see the fit",
    text: "How the experience you recorded relates to what the ad asks for.",
  },
];

// AC 5.1.1/5.1.2: a single screen that moves through paste -> analysing ->
// results, rather than separate routes - nothing about the transition
// needs its own URL (no back/forward semantics worth preserving), and it
// keeps the just-analysed result in hand without threading an id through
// this app's simple hash router.
export default function AnalyseJobDescription() {
  const [rawText, setRawText] = useState("");
  const [stage, setStage] = useState("input"); // input | analysing | results
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const trimmedLength = rawText.trim().length;
  const tooShort = trimmedLength > 0 && trimmedLength < MIN_CHARACTERS;
  const canAnalyse = trimmedLength >= MIN_CHARACTERS && trimmedLength <= MAX_CHARACTERS;

  const handleAnalyse = async () => {
    if (!canAnalyse) return;
    setError("");
    setStage("analysing");
    try {
      const jobDescription = await api.createJobDescription(rawText);
      const hasRequirements =
        jobDescription.extracted_skills.length > 0 ||
        jobDescription.extracted_responsibilities.length > 0 ||
        jobDescription.min_years_experience != null;
      if (!hasRequirements) {
        setError("We couldn't find clear requirements in this text. Please check that you've pasted a job description.");
        setStage("input");
        return;
      }
      setResult(jobDescription);
      setStage("results");
    } catch (err) {
      if (err instanceof ApiError && err.code === "TIMEOUT") {
        setError("This is taking longer than expected. Please try again.");
      } else {
        setError("We couldn't find clear requirements in this text. Please check that you've pasted a job description.");
      }
      setStage("input");
    }
  };

  if (stage === "results" && result) {
    return (
      <>
        <TopNav />
        <div className="ajd-page">
          <span className="ajd-eyebrow">WHAT THIS JOB ASKS FOR</span>
          <h1 className="ajd-heading">{result.role_title_guess || "This role"}</h1>
          <p className="ajd-subheading">
            From the job description you pasted. Check it reads right before comparing it with your profile.
          </p>

          <div className="ajd-results-grid">
            <div className="ajd-card">
              <span className="ajd-card-label">TECHNICAL SKILLS</span>
              <div className="ajd-pills">
                {result.extracted_skills.filter((s) => s.category === "technical").map((s) => (
                  <span key={s.label} className="ajd-pill">{s.label}</span>
                ))}
                {result.extracted_skills.every((s) => s.category !== "technical") && (
                  <span className="ajd-empty">None found.</span>
                )}
              </div>
            </div>

            <div className="ajd-card">
              <span className="ajd-card-label">RESPONSIBILITIES</span>
              <div className="ajd-list">
                {result.extracted_responsibilities.length > 0 ? (
                  result.extracted_responsibilities.map((r) => <p key={r}>{r}</p>)
                ) : (
                  <span className="ajd-empty">None found.</span>
                )}
              </div>
            </div>

            <div className="ajd-card">
              <span className="ajd-card-label">SOFT SKILLS</span>
              <div className="ajd-pills">
                {result.extracted_skills.filter((s) => s.category === "soft").map((s) => (
                  <span key={s.label} className="ajd-pill">{s.label}</span>
                ))}
                {result.extracted_skills.every((s) => s.category !== "soft") && (
                  <span className="ajd-empty">None found.</span>
                )}
              </div>
            </div>

            {result.min_years_experience != null && (
              <div className="ajd-card">
                <span className="ajd-card-label">EXPERIENCE</span>
                <p className="ajd-experience">
                  {result.min_years_experience}+ years of experience.
                </p>
              </div>
            )}
          </div>

          <div className="ajd-footer">
            <span className="ajd-footer-note">Saved to your dashboard.</span>
            <div className="ajd-footer-actions">
              <button type="button" className="ajd-btn-outline" onClick={() => setStage("input")}>
                Back
              </button>
              <button
                type="button"
                className="ajd-btn-primary"
                onClick={() => {
                  setCurrentJobDescriptionId(result.job_description_id);
                  navigate("/job-description-comparison");
                }}
              >
                Compare With My Profile <span aria-hidden="true">›</span>
              </button>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <TopNav />
      {stage === "analysing" && <LoadingPopup text="Reading the job description…" caption="This can take up to half a minute." />}
      <div className="ajd-page">
        <span className="ajd-eyebrow">ANALYSE A JOB DESCRIPTION</span>
        <h1 className="ajd-heading">See how your experience relates to a role</h1>

        <div className="ajd-input-grid">
          <div className="ajd-card">
            <span className="ajd-card-label">Paste the job description</span>
            <textarea
              className="ajd-textarea"
              placeholder="Paste the full ad here, including responsibilities and requirements."
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              disabled={stage === "analysing"}
              maxLength={MAX_CHARACTERS}
            />
            <div className="ajd-char-row">
              <span>Between {MIN_CHARACTERS} and {MAX_CHARACTERS.toLocaleString()} characters.</span>
              <span>{trimmedLength} / {MAX_CHARACTERS.toLocaleString()} characters</span>
            </div>
          </div>

          <div className="ajd-card ajd-how">
            <span className="ajd-card-label">HOW THIS WORKS</span>
            {howThisWorks.map((item, i) => (
              <div key={item.title} className={`ajd-how-item ${i > 0 ? "ajd-how-item--divided" : ""}`}>
                <strong>{item.title}</strong>
                <p>{item.text}</p>
              </div>
            ))}
          </div>
        </div>

        {error && <p className="ajd-error">{error}</p>}

        <div className="ajd-footer">
          <span className="ajd-footer-note">
            {stage === "analysing"
              ? "This usually takes a few seconds."
              : tooShort
                ? "This looks too short to be a full job description. Please paste the complete advertisement."
                : canAnalyse
                  ? "Ready to analyse."
                  : "Analyse unlocks once you have pasted a job description."}
          </span>
          <div className="ajd-footer-actions">
            <button type="button" className="ajd-btn-outline" onClick={() => navigate("/choose-your-path")}>
              Back
            </button>
            <button
              type="button"
              className="ajd-btn-primary"
              onClick={handleAnalyse}
              disabled={!canAnalyse || stage === "analysing"}
            >
              {stage === "analysing" ? "Analysing…" : "Analyse"} {stage !== "analysing" && <span aria-hidden="true">›</span>}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
