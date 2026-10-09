import { ArrowRightIcon } from "../icons";

function SkillsUsed({ skills }) {
  if (!skills?.length) return null; // AC 4.4.5: no tags, no skills line
  return (
    <div className="pa-card pa-skills-used">
      <strong>Skills used in this activity</strong>
      {skills.map((skill) => <span key={skill} className="pa-skill-chip">{skill}</span>)}
    </div>
  );
}

/**
 * Reflective feedback after an activity. Nothing is graded: no score, no
 * right/wrong labels, and for Drag and Drop no count of phrases that fit -
 * "What would work better" appears only under a phrase that doesn't.
 */
function FeedbackLines({ lines }) {
  return lines.map((line) => <p className="pa-feedback-text" key={line}>{line}</p>);
}

// Feedback stored by the backend for a real question (what_worked_well,
// trade_offs, areas_to_consider, skill_to_explore). A section with nothing
// in it is left out rather than shown empty.
function StoredFeedback({ feedback }) {
  if (!feedback) {
    return (
      <div className="pa-card pa-feedback-card">
        <span className="pa-feedback-label">YOUR RESPONSE IS SAVED</span>
        <p className="pa-feedback-text">Feedback isn&rsquo;t available for this one right now. You can carry on.</p>
      </div>
    );
  }
  const skill = feedback.skill_to_explore;
  return (
    <>
      {feedback.what_worked_well.length > 0 && (
        <div className="pa-card pa-feedback-card">
          <span className="pa-feedback-label pa-feedback-label--blue">WHAT WORKED WELL</span>
          <FeedbackLines lines={feedback.what_worked_well} />
        </div>
      )}
      {feedback.trade_offs.length > 0 && (
        <div className="pa-card pa-feedback-card">
          <span className="pa-feedback-label">TRADE-OFFS</span>
          <FeedbackLines lines={feedback.trade_offs} />
        </div>
      )}
      {feedback.areas_to_consider.length > 0 && (
        <div className="pa-card pa-feedback-card">
          <span className="pa-feedback-label">CONSIDER</span>
          <FeedbackLines lines={feedback.areas_to_consider} />
        </div>
      )}
      {skill && (
        <div className="pa-card pa-feedback-card">
          <span className="pa-feedback-label pa-feedback-label--violet">SKILL TO EXPLORE</span>
          <h2 className="pa-feedback-skill">{skill.skill}</h2>
          <p className="pa-feedback-why">{skill.why_relevant}</p>
        </div>
      )}
    </>
  );
}

export default function PracticeFeedback({
  activity, answer, feedback, dragDropFeedback, areaLabel, isLast, continueLabel, onContinue,
}) {
  const isDragDrop = activity.type === "drag_and_drop";
  // Real multiple-choice questions bring their feedback from the backend
  // (possibly null); the mock Code Review reads it from its own options.
  const isStored = feedback !== undefined;
  const chosen = isDragDrop || isStored ? null : activity.options.find((option) => option.id === answer);

  return (
    <>
      <main className="pa-body">
        <span className="pa-eyebrow">{areaLabel.toUpperCase()}</span>
        <h1 className="pa-heading">Your practice feedback</h1>

        {isDragDrop ? (
          <>
            <div className="pa-card pa-feedback-card">
              <span className="pa-feedback-label pa-feedback-label--blue">YOUR MESSAGE</span>
              <p className="pa-feedback-text">{dragDropFeedback.message}</p>
            </div>
            <div className="pa-card pa-feedback-card">
              <span className="pa-feedback-label">HOW EACH PHRASE COMES ACROSS</span>
              {dragDropFeedback.phrases.map((phrase) => (
                <div className="pa-phrase-row" key={phrase.id}>
                  <span className="pa-phrase-chip">{phrase.text}</span>
                  <div>
                    <p>{phrase.comesAcross}</p>
                    {phrase.better && (
                      <>
                        <span className="pa-eyebrow pa-better-label">WHAT WOULD WORK BETTER</span>
                        <p>{phrase.better}</p>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : isStored ? (
          <StoredFeedback feedback={feedback} />
        ) : (
          <>
            <div className="pa-card pa-feedback-card">
              <span className="pa-feedback-label pa-feedback-label--blue">WHAT WORKED WELL</span>
              <p className="pa-feedback-text">{chosen.workedWell}</p>
            </div>
            <div className="pa-card pa-feedback-card">
              <span className="pa-feedback-label">CONSIDER</span>
              <p className="pa-feedback-text">{chosen.consider}</p>
            </div>
            <div className="pa-card pa-feedback-card">
              <span className="pa-feedback-label pa-feedback-label--violet">SKILL TO EXPLORE</span>
              <h2 className="pa-feedback-skill">{activity.skillToExplore.skill}</h2>
              <p className="pa-feedback-why">{activity.skillToExplore.why}</p>
            </div>
          </>
        )}

        <SkillsUsed skills={activity.skillsUsed} />
      </main>

      <div className="pa-footer">
        <span className="pa-footer-note">Nothing here is graded.</span>
        <button type="button" className="pa-btn-primary" onClick={onContinue}>
          {continueLabel || (isLast ? "Continue" : "Back to the floor")} <ArrowRightIcon size={16} />
        </button>
      </div>
    </>
  );
}

// Shown while an activity is being prepared (AC 4.4.6: "Setting up this
// situation…"), in the same layout the activity will have.
export function ActivitySkeleton({ areaLabel }) {
  return (
    <>
      <main className="pa-body" aria-busy="true">
        <span className="pa-eyebrow">{areaLabel.toUpperCase()}</span>
        <div className="pa-skel pa-skel--heading" />
        <div className="pa-columns">
          <div className="pa-card">
            <div className="pa-person">
              <span className="pa-skel pa-skel--avatar" />
              <div className="pa-skel-lines">
                <span className="pa-skel pa-skel--line-short" />
                <span className="pa-skel pa-skel--line" />
              </div>
            </div>
            <div className="pa-skel pa-skel--block" />
            <span className="pa-skel pa-skel--line-wide" />
            <span className="pa-skel pa-skel--line" />
          </div>
          <div className="pa-card">
            <h2 className="pa-question pa-setting-up"><span className="pa-setting-dot" /> Setting up this situation…</h2>
            <p className="pa-question-caption">This takes a few seconds.</p>
            <div className="pa-skel pa-skel--option" />
            <div className="pa-skel pa-skel--option" />
            <div className="pa-skel pa-skel--option" />
          </div>
        </div>
      </main>
      <div className="pa-footer">
        <span className="pa-footer-note">Your situation will open here in a moment.</span>
        <button type="button" className="pa-btn-primary" disabled>Reply</button>
      </div>
    </>
  );
}
