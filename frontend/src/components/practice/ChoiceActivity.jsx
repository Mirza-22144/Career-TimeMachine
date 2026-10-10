import { useState } from "react";
import { ArrowRightIcon, CheckIcon, FileTextIcon, LightbulbIcon } from "../icons";

// The hint stays hidden until she asks for it (AC 4.4.4).
export function HintToggle({ hint }) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <>
      <button type="button" className="pa-hint-link" onClick={() => setIsOpen((v) => !v)} aria-expanded={isOpen}>
        <LightbulbIcon size={15} color="#6D28D9" /> {isOpen ? "Hide hint" : "Need a hint?"}
      </button>
      {isOpen && (
        <div className="pa-hint">
          <strong>Hint</strong>
          {(Array.isArray(hint) ? hint : [hint]).map((line) => <p key={line}>{line}</p>)}
        </div>
      )}
    </>
  );
}

/**
 * Multiple Choice and Code Review share this: a left card (a colleague's
 * question, or a read-only piece of code) and one single-selection
 * question on the right. Nothing is preselected and no option is marked
 * right or wrong.
 */
export default function ChoiceActivity({ activity, areaLabel, isSubmitting = false, submitError = "", onSubmit }) {
  const [selectedId, setSelectedId] = useState(null);
  const isCode = activity.type === "code_review";
  // Multiple choice describes a situation on the left; code review shows code.
  const isSituation = !isCode && Boolean(activity.situation);
  const submitLabel = isCode || isSituation ? "Submit" : "Reply";
  const hasHint = Array.isArray(activity.hint) ? activity.hint.length > 0 : Boolean(activity.hint);

  return (
    <>
      <main className="pa-body">
        <span className="pa-eyebrow">{areaLabel.toUpperCase()}</span>
        <h1 className="pa-heading">{activity.title}</h1>

        <div className={`pa-columns ${isCode ? "pa-columns--code" : ""}`}>
          {isCode ? (
            <div className="pa-card pa-card--flush">
              <div className="pa-code-header">
                <FileTextIcon size={15} color="#6D28D9" />
                <code>{activity.language}</code>
                <span>Read only · never run</span>
              </div>
              <pre className="pa-code" aria-label={`${activity.language} code, read only`}>
                {activity.code.map((line, index) => (
                  <span className="pa-code-line" key={activity.firstLine + index}>
                    <span className="pa-code-number">{activity.firstLine + index}</span>
                    <span>{line}</span>
                  </span>
                ))}
              </pre>
              <div className="pa-code-from">
                <span className="pa-eyebrow">THE SITUATION</span>
                <p>{activity.situation}</p>
              </div>
            </div>
          ) : isSituation ? (
            <div className="pa-card">
              <span className="pa-eyebrow">THE SITUATION</span>
              <p className="pa-situation">{activity.situation}</p>
            </div>
          ) : (
            <div className="pa-card">
              <div className="pa-person">
                <span className="pa-avatar">{activity.person.initial}</span>
                <div>
                  <strong>{activity.person.name}</strong>
                  <span>{activity.person.role}</span>
                </div>
              </div>
              <blockquote className="pa-quote">{activity.quote}</blockquote>
              <p className="pa-context">{activity.context}</p>
            </div>
          )}

          <div className="pa-card">
            <h2 className="pa-question">{activity.prompt}</h2>
            {activity.promptCaption && <p className="pa-question-caption">{activity.promptCaption}</p>}
            <div className="pa-options" role="radiogroup" aria-label={activity.prompt}>
              {activity.options.map((option) => {
                const isSelected = option.id === selectedId;
                return (
                  <button
                    type="button"
                    key={option.id}
                    role="radio"
                    aria-checked={isSelected}
                    className={`pa-option ${isSelected ? "pa-option--selected" : ""}`}
                    disabled={isSubmitting}
                    onClick={() => setSelectedId(option.id)}
                  >
                    <span className={`pa-radio ${isSelected ? "pa-radio--on" : ""}`}>
                      {isSelected && <CheckIcon size={11} />}
                    </span>
                    {option.text}
                  </button>
                );
              })}
            </div>
            {hasHint && <HintToggle hint={activity.hint} />}
          </div>
        </div>
      </main>

      <div className="pa-footer">
        <span className={`pa-footer-note ${submitError ? "pa-footer-note--error" : ""}`} role={submitError ? "alert" : undefined}>
          {submitError
            || (selectedId
              ? `You can change your ${isCode || isSituation ? "choice before you submit" : "reply before you send it"}.`
              : isCode || isSituation ? "Choose one option to submit." : "Choose a reply to continue.")}
        </span>
        <button
          type="button"
          className="pa-btn-primary"
          disabled={!selectedId || isSubmitting}
          onClick={() => onSubmit(selectedId)}
        >
          {isSubmitting ? "Saving…" : submitLabel} {selectedId && !isSubmitting && <ArrowRightIcon size={16} />}
        </button>
      </div>
    </>
  );
}
