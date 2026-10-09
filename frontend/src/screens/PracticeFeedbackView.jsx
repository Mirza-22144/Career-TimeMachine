import { useEffect, useState } from "react";
import "../styles/PracticeActivity.css";
import TopNav from "../components/TopNav";
import LoadingPopup from "../components/LoadingPopup";
import PracticeFeedback from "../components/practice/PracticeFeedback";
import { WORKPLACE_AREAS, getPrimaryAreaId } from "../mockData/workplaceAreas.js";
import { loadMockActivities } from "../mockData/practiceSession.js";
import { getLocalFeedback, getViewingFeedbackId } from "../practiceHistory.js";
import { parseApiFeedbackId, toChoiceActivity, toDragDropActivity, toDragDropFeedback } from "../practiceAdapters.js";
import { api } from "../api.js";
import { navigate } from "../navigate.js";

const areaLabel = (areaId) => WORKPLACE_AREAS.find((area) => area.id === areaId)?.label || "";

// A multiple-choice question: her stored feedback from the backend.
async function loadStored({ sessionId, scenarioId }) {
  const session = await api.getPracticeSession(sessionId);
  const scenario = session.scenarios.find((item) => item.scenario_id === scenarioId);
  if (!scenario || scenario.status !== "completed") return null;
  if (scenario.activity_type === "drag_and_drop") {
    const activity = toDragDropActivity(scenario);
    return {
      activity,
      dragDropFeedback: toDragDropFeedback(scenario, activity),
      roleLabel: session.role.label,
      areaLabel: areaLabel("project_delivery_board"),
    };
  }
  return {
    activity: toChoiceActivity(scenario),
    feedback: scenario.feedback,
    roleLabel: session.role.label,
    areaLabel: areaLabel(getPrimaryAreaId(session.role.id)),
  };
}

// Code Review: still mock, kept in this browser.
async function loadLocal(id) {
  const entry = getLocalFeedback(id);
  if (!entry) return null;
  const activity = (await loadMockActivities()).find((item) => item.id === entry.activityId);
  if (!activity) return null;
  return { activity, answer: entry.answer, roleLabel: entry.roleLabel, areaLabel: areaLabel(activity.areaId) };
}

/**
 * "View feedback" from the dashboard (AC 3.4.1): re-reads the feedback for
 * an activity she has already completed. It reuses the same feedback
 * component as the practice flow, so there is one feedback layout to
 * maintain and no extra state in the practice screen.
 */
export default function PracticeFeedbackView() {
  const [id] = useState(() => getViewingFeedbackId());
  const [view, setView] = useState(null);
  const [status, setStatus] = useState(id ? "loading" : "none"); // loading | ready | none

  useEffect(() => {
    if (!id) return;
    const stored = parseApiFeedbackId(id);
    (stored ? loadStored(stored) : loadLocal(id))
      .then((found) => {
        setView(found);
        setStatus(found ? "ready" : "none");
      })
      .catch(() => setStatus("none"));
  }, [id]);

  return (
    <>
      <TopNav />
      <div className="pa-page">
        <div className="pa-topbar">
          <button type="button" className="pa-back" onClick={() => navigate("/dashboard")}>
            <span aria-hidden="true">&larr;</span> Back to dashboard
          </button>
          {view && <span className="pa-breadcrumb">{view.roleLabel} · {view.areaLabel}</span>}
        </div>
        {status === "ready" && (
          <PracticeFeedback
            activity={view.activity}
            answer={view.answer}
            feedback={view.feedback}
            dragDropFeedback={view.dragDropFeedback}
            areaLabel={view.areaLabel}
            continueLabel="Back to dashboard"
            onContinue={() => navigate("/dashboard")}
          />
        )}
        {status === "loading" && <LoadingPopup text="Loading your feedback…" />}
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
