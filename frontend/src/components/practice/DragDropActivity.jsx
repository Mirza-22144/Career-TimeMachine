import { useEffect, useState } from "react";
import { ArrowRightIcon } from "../icons";
import { HintToggle } from "./ChoiceActivity";

/**
 * Drag and Drop (US 4.6): complete a workplace message by placing phrases
 * into its gaps. Works three ways, so it never depends on dragging:
 * drag a phrase onto a gap; select a phrase then select a gap (mouse,
 * touch or keyboard); select a filled gap to send its phrase back.
 */
export default function DragDropActivity({ activity, areaLabel, onSubmit }) {
  const gapCount = activity.message.filter((part) => typeof part !== "string").length;
  const [placed, setPlaced] = useState(() => Array(gapCount).fill(null)); // gap index -> phrase id
  const [selectedId, setSelectedId] = useState(null);
  const [draggingId, setDraggingId] = useState(null);
  const [overGap, setOverGap] = useState(null);
  const [status, setStatus] = useState("Drag a phrase into a gap, or select a phrase and then a gap.");

  const phraseById = (id) => activity.phrases.find((p) => p.id === id);
  const available = activity.phrases.filter((p) => !placed.includes(p.id));
  const isComplete = placed.every((id) => id !== null);

  useEffect(() => {
    if (!selectedId) return undefined;
    const onKeyDown = (e) => {
      if (e.key === "Escape") {
        setSelectedId(null);
        setStatus("Selection cancelled.");
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [selectedId]);

  // Puts a phrase in a gap. A phrase already in that gap goes back to the
  // list; a phrase moved from another gap leaves that gap empty.
  const place = (phraseId, gapIndex) => {
    const previous = placed[gapIndex];
    const next = placed.map((id) => (id === phraseId ? null : id));
    next[gapIndex] = phraseId;
    setPlaced(next);
    setSelectedId(null);
    const text = phraseById(phraseId).text;
    if (next.every((id) => id !== null)) setStatus("All three gaps are filled.");
    else if (previous && previous !== phraseId) {
      setStatus(`Gap ${gapIndex + 1} now reads “${text}”. “${phraseById(previous).text}” is back in your phrases.`);
    } else setStatus(`“${text}” placed in gap ${gapIndex + 1}.`);
  };

  const handleGapClick = (gapIndex) => {
    if (selectedId) {
      place(selectedId, gapIndex);
    } else if (placed[gapIndex]) {
      const text = phraseById(placed[gapIndex]).text;
      setPlaced(placed.map((id, i) => (i === gapIndex ? null : id)));
      setStatus(`“${text}” is back in your phrases.`);
    }
  };

  const handleDrop = (e, gapIndex) => {
    e.preventDefault();
    const phraseId = e.dataTransfer.getData("text/plain") || draggingId;
    setOverGap(null);
    setDraggingId(null);
    if (phraseId && phraseById(phraseId)) place(phraseId, gapIndex);
  };

  const dragProps = (phraseId) => ({
    draggable: true,
    onDragStart: (e) => {
      e.dataTransfer.setData("text/plain", phraseId);
      e.dataTransfer.effectAllowed = "move";
      setDraggingId(phraseId);
      setSelectedId(null);
    },
    // Dropped outside any gap: nothing was placed, so it simply stays put.
    onDragEnd: () => {
      setDraggingId(null);
      setOverGap(null);
    },
  });

  return (
    <>
      <main className="pa-body">
        <span className="pa-eyebrow">{areaLabel.toUpperCase()}</span>
        <h1 className="pa-heading">{activity.title}</h1>
        <p className="pa-subheading">{activity.instruction}</p>

        <div className="pa-card pa-message-card">
          <div className="pa-message-to"><span>To</span> {activity.to}</div>
          <p className="pa-message">
            {activity.message.map((part, index) => {
              if (typeof part === "string") return <span key={index}>{part}</span>;
              const phraseId = placed[part.gap];
              const isOver = overGap === part.gap;
              return (
                <button
                  type="button"
                  key={index}
                  className={`pa-gap ${phraseId ? "pa-gap--filled" : ""} ${isOver ? "pa-gap--over" : ""} ${selectedId && !phraseId ? "pa-gap--target" : ""}`}
                  aria-label={phraseId ? `Gap ${part.gap + 1}: ${phraseById(phraseId).text}` : `Gap ${part.gap + 1}, empty`}
                  onClick={() => handleGapClick(part.gap)}
                  onDragOver={(e) => {
                    e.preventDefault();
                    if (overGap !== part.gap) {
                      setOverGap(part.gap);
                      setStatus(`Over gap ${part.gap + 1}. Release to place it there.`);
                    }
                  }}
                  onDragLeave={() => setOverGap(null)}
                  onDrop={(e) => handleDrop(e, part.gap)}
                  {...(phraseId ? dragProps(phraseId) : {})}
                >
                  {phraseId
                    ? phraseById(phraseId).text
                    : isOver ? "Drop here" : selectedId ? "Place here" : `Gap ${part.gap + 1}`}
                </button>
              );
            })}
          </p>
        </div>

        <h2 className="pa-phrases-label">Phrases</h2>
        <div className="pa-phrases">
          {available.map((phrase) => (
            <button
              type="button"
              key={phrase.id}
              className={`pa-phrase ${selectedId === phrase.id ? "pa-phrase--selected" : ""} ${draggingId === phrase.id ? "pa-phrase--dragging" : ""}`}
              aria-pressed={selectedId === phrase.id}
              onClick={() => {
                const next = selectedId === phrase.id ? null : phrase.id;
                setSelectedId(next);
                setStatus(next ? "Phrase selected. Choose a gap to place it, or press Escape to cancel." : "Selection cancelled.");
              }}
              {...dragProps(phrase.id)}
            >
              <span className="pa-grip" aria-hidden="true">⠿</span>
              {phrase.text}
              {selectedId === phrase.id && <span className="pa-phrase-tag">Selected</span>}
            </button>
          ))}
        </div>
        <p className="pa-status" role="status" aria-live="polite">{status}</p>

        <div className="pa-hint-wrap">
          <HintToggle hint={activity.hint} />
        </div>
      </main>

      <div className="pa-footer">
        <span className="pa-footer-note">
          {isComplete ? "Every gap is filled. You can still swap phrases." : "Submit unlocks when every gap is filled."}
        </span>
        <button type="button" className="pa-btn-primary" disabled={!isComplete} onClick={() => onSubmit(placed)}>
          Submit {isComplete && <ArrowRightIcon size={16} />}
        </button>
      </div>
    </>
  );
}
