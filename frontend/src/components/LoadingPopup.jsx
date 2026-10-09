import "../styles/LoadingPopup.css";

/**
 * The one loading state for the whole app: a small card over a dimmed page,
 * shown whenever a screen is waiting for its data. It fades in after a
 * short delay, so a load that finishes straight away never flashes it.
 */
export default function LoadingPopup({ text = "Loading…", caption = "This takes a few seconds." }) {
  return (
    <div className="lp-overlay" role="status" aria-live="polite">
      <div className="lp-card">
        <span className="lp-ring" aria-hidden="true">
          <span className="lp-ring-dot" />
        </span>
        <div>
          <strong className="lp-text">{text}</strong>
          <span className="lp-caption">{caption}</span>
        </div>
      </div>
    </div>
  );
}
