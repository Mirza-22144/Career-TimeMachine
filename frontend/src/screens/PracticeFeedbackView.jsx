import { useEffect, useState } from "react";
import "../styles/PracticeActivity.css";
import TopNav from "../components/TopNav";
import PracticeFeedback from "../components/practice/PracticeFeedback";
import { WORKPLACE_AREAS } from "../mockData/workplaceAreas.js";
import { loadPracticeSession } from "../mockData/practiceSession.js";
import { getViewingFeedback } from "../practiceHistory.js";
import { navigate } from "../navigate.js";

/**
 * "View feedback" from the dashboard (AC 3.4.1): re-reads the feedback for
 * an activity she has already completed. It reuses the same feedback
 * component as the practice flow, fed with her stored answer, so there is
 * one feedback layout to maintain and no extra state in the practice screen.
 */
export default function PracticeFeedbackView() {
  const [entry] = useState(() => getViewingFeedback());
  const [activity, setActivity] = useState(null);
  const [status, setStatus] = useState(entry ? "loading" : "none"); // loading | ready | none

  useEffect(() => {
    if (!entry) return;
    loadPracticeSession()
      .then((session) => {
        const found = session.activities.find((item) => item.id === entry.activityId);
        setActivity(found || null);
        setStatus(found ? "ready" : "none");
      })
      .catch(() => setStatus("none"));
  }, [entry]);

  const areaLabel = activity ? WORKPLACE_AREAS.find((a) => a.id === activity.areaId).label : "";

  return (
    <>
      <TopNav />
      <div className="pa-page">
        <div className="pa-topbar">
          <button type="button" className="pa-back" onClick={() => navigate("/dashboard")}>
            <span aria-hidden="true">&larr;</span> Back to dashboard
          </button>
          {entry && <span className="pa-breadcrumb">{entry.roleLabel} · {areaLabel}</span>}
        </div>
        {status === "ready" && (
          <PracticeFeedback
            activity={activity}
            answer={entry.answer}
            areaLabel={areaLabel}
            continueLabel="Back to dashboard"
            onContinue={() => navigate("/dashboard")}
          />
        )}
        {status === "loading" && <main className="pa-body"><p className="pa-loading">Loading your feedback…</p></main>}
        {status === "none" && (
          <main className="pa-body">
            <p className="pa-loading">We couldn&rsquo;t find feedback for this activity.</p>
            <button type="button" className="pa-btn-outline" onClick={() => navigate("/dashboard")}>
              Back to dashboard
            </button>
          </main>
        )}
      </div>
    </>
  );
}
