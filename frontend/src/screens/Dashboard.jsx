import { useEffect, useState } from "react";
import "../styles/Dashboard.css";
import "../styles/AccessTokenModal.css";
import TopNav from "../components/TopNav";
import LoadingPopup from "../components/LoadingPopup";
import { ArrowRightIcon, CheckIcon } from "../components/icons";
import { api } from "../api.js";
import { navigate } from "../navigate.js";
import { sendToProfileSetup } from "../resumeStep.js";
import { setCurrentJobDescriptionId } from "../currentJob.js";
import { apiFeedbackId, setViewingFeedback } from "../practiceAdapters.js";

const ACTIVITY_TYPE_LABELS = {
  multiple_choice: "Multiple Choice",
  written_response: "Written Response",
  code_review: "Code Review",
  drag_and_drop: "Drag and Drop",
};

const shortDate = (iso) =>
  new Date(iso).toLocaleDateString("en-AU", { day: "numeric", month: "short" });

/**
 * US 3.4 dashboard ("Your progress"). Everything shown is real: completed
 * activities from GET /practice-sessions/recent-activities and saved job
 * descriptions from GET /job-descriptions (removable, AC 3.5.1).
 *
 * The "next step" card (AC 3.4.2) follows the role she selected to practise
 * on Your Roadmap (GET /roadmap). Only that one selected role is known -
 * there is no history of earlier role choices or their dates yet.
 */
export default function Dashboard() {
  const [isChecking, setIsChecking] = useState(true);
  // Each list loads and fails on its own (AC 3.4.1: "keep the rest of the
  // page available"). null = loading, "error" = failed, array = loaded.
  const [activities, setActivities] = useState(null);
  const [jobDescriptions, setJobDescriptions] = useState(null);
  // The role selected on Your Roadmap, or null if none (or it couldn't load).
  const [selectedRole, setSelectedRole] = useState(null);
  // Every role she has chosen to practise, with the date (GET /roadmap).
  const [chosenRoles, setChosenRoles] = useState([]);
  // The next-step card depends on the roadmap, so the page waits for it.
  const [isRoadmapSettled, setIsRoadmapSettled] = useState(false);
  const [removeTarget, setRemoveTarget] = useState(null);
  const [isRemoving, setIsRemoving] = useState(false);
  const [removeError, setRemoveError] = useState("");
  const [toast, setToast] = useState("");

  const loadActivities = () => {
    setActivities(null);
    api.getRecentActivities().then(setActivities).catch(() => setActivities("error"));
  };
  const loadJobDescriptions = () => {
    setJobDescriptions(null);
    api.listJobDescriptions().then(setJobDescriptions).catch(() => setJobDescriptions("error"));
  };

  useEffect(() => {
    let cancelled = false;
    api
      .getProfile()
      .then((profile) => {
        if (cancelled) return;
        if (!profile.confirmed) {
          sendToProfileSetup(profile);
          return;
        }
        setIsChecking(false);
        api.getRecentActivities().then(setActivities).catch(() => setActivities("error"));
        api.listJobDescriptions().then(setJobDescriptions).catch(() => setJobDescriptions("error"));
        api
          .getRoadmap()
          .then((roadmap) => {
            const roles = [roadmap.previous_role, ...roadmap.suggested_roles];
            setSelectedRole(roles.find((r) => r && r.role_id === roadmap.selected_role_id) || null);
            setChosenRoles(roadmap.chosen_roles);
          })
          .catch(() => setSelectedRole(null))
          .finally(() => setIsRoadmapSettled(true));
      })
      .catch(() => {
        if (!cancelled) navigate("/your-story");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 4000);
    return () => clearTimeout(timer);
  }, [toast]);

  const handleRemove = async () => {
    setIsRemoving(true);
    setRemoveError("");
    try {
      await api.deleteJobDescription(removeTarget.job_description_id);
      setJobDescriptions((list) => list.filter((jd) => jd.job_description_id !== removeTarget.job_description_id));
      setRemoveTarget(null);
      setToast("Job description removed.");
    } catch {
      setRemoveError("We couldn't remove this job description. Please try again.");
    } finally {
      setIsRemoving(false);
    }
  };

  const isLoading = isChecking || !isRoadmapSettled || activities === null || jobDescriptions === null;
  const steps = selectedRole?.skills_could_explore || [];
  const nextSkill = steps.find((skill) => skill.status === "next");
  // Newest first (the API already sorts them).
  const recent = Array.isArray(activities)
    ? activities.map((a) => ({
        key: `${a.session_id}-${a.scenario_id}`,
        title: a.title,
        type: a.activity_type,
        when: a.completed_at,
        feedbackId: apiFeedbackId(a.session_id, a.scenario_id),
      }))
    : [];
  // The selected role always appears, even before its history row exists.
  const roleRows = chosenRoles.length > 0
    ? chosenRoles
    : selectedRole ? [{ role_id: selectedRole.role_id, role_label: selectedRole.role_label, chosen_at: null }] : [];
  const nothingYet =
    !selectedRole &&
    recent.length === 0 &&
    Array.isArray(activities) && activities.length === 0 &&
    Array.isArray(jobDescriptions) && jobDescriptions.length === 0;

  return (
    <>
      <TopNav />
      <div className="dash-page">
        <h1 className="dash-heading">Your progress</h1>

        {isLoading && <LoadingPopup text="Loading your progress…" />}

        {!isLoading && nothingYet && (
          <>
            <p className="dash-subheading">Nothing here yet. Your first step is to choose a path.</p>
            <div className="dash-empty">
              <h2 className="dash-empty-title">You haven&rsquo;t started yet.</h2>
              <p className="dash-empty-text">
                Choose a path to build your roadmap. Your activities, saved job descriptions and roles will appear
                here.
              </p>
              <button type="button" className="dash-btn-primary" onClick={() => navigate("/choose-your-path")}>
                Choose Your Path <ArrowRightIcon size={16} />
              </button>
            </div>
          </>
        )}

        {!isLoading && !nothingYet && (
          <>
            <p className="dash-subheading">Here is where you are. One step is enough for today.</p>

            {!selectedRole ? (
              <div className="dash-card dash-next">
                <div>
                  <span className="dash-eyebrow">YOUR NEXT STEP</span>
                  <h2 className="dash-next-title">Choose a path to build your roadmap.</h2>
                </div>
                <button type="button" className="dash-btn-primary" onClick={() => navigate("/choose-your-path")}>
                  Choose Your Path <ArrowRightIcon size={16} />
                </button>
              </div>
            ) : (
              <div className="dash-card dash-next-card">
                <div className="dash-next">
                  <div>
                    <span className="dash-eyebrow">
                      YOUR NEXT STEP · {selectedRole.role_label.toUpperCase()} ROADMAP
                    </span>
                    <h2 className="dash-next-title">
                      {nextSkill
                        ? `Practise a situation that uses ${nextSkill.label}`
                        : steps.length > 0
                          ? "You’ve practised every skill to explore for this roadmap."
                          : `Practise as a ${selectedRole.role_label}`}
                    </h2>
                  </div>
                  <div className="dash-next-actions">
                    <button type="button" className="dash-btn-outline" onClick={() => navigate("/your-roadmap")}>
                      View Roadmap
                    </button>
                    {(nextSkill || steps.length === 0) && (
                      <button type="button" className="dash-btn-primary" onClick={() => navigate("/workplace-scenario")}>
                        Continue <ArrowRightIcon size={16} />
                      </button>
                    )}
                  </div>
                </div>
                {steps.length > 0 && (
                  <div className="dash-steps">
                    {steps.map((skill) => (
                      <div key={skill.id} className={`dash-step dash-step--${skill.status}`}>
                        <span className="dash-step-dot">
                          {skill.status === "practised" && <CheckIcon size={12} />}
                        </span>
                        <span className="dash-step-label">{skill.label}</span>
                        <span className="dash-step-status">
                          {skill.status === "practised" && `Practised ${shortDate(skill.practised_on)}`}
                          {skill.status === "next" && "Next"}
                          {skill.status === "later" && "Later"}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="dash-columns">
              <div className="dash-card">
                <h2 className="dash-card-title">Recent practice</h2>
                {activities === "error" ? (
                  <div className="dash-row dash-row--message">
                    <span>We couldn&rsquo;t load this. Please try again.</span>
                    <button type="button" className="dash-link" onClick={loadActivities}>Try Again</button>
                  </div>
                ) : recent.length === 0 ? (
                  <div className="dash-row dash-row--message">
                    <span>No completed activities yet.</span>
                  </div>
                ) : (
                  recent.map((activity) => (
                    <div className="dash-row" key={activity.key}>
                      <div>
                        <span className="dash-row-title">{activity.title}</span>
                        <span className="dash-row-meta">
                          {ACTIVITY_TYPE_LABELS[activity.type] || activity.type} · {shortDate(activity.when)}
                        </span>
                      </div>
                      {activity.feedbackId && (
                        <button
                          type="button"
                          className="dash-link"
                          onClick={() => {
                            setViewingFeedback(activity.feedbackId);
                            navigate("/practice-feedback");
                          }}
                        >
                          View feedback <span aria-hidden="true">›</span>
                        </button>
                      )}
                    </div>
                  ))
                )}
              </div>

              <div className="dash-card">
                <h2 className="dash-card-title">Your roadmaps</h2>
                {roleRows.map((role) => (
                  <button
                    type="button"
                    key={role.role_id}
                    className="dash-row dash-row--link"
                    onClick={() => navigate("/your-roadmap")}
                  >
                    <div>
                      <span className="dash-row-title">{role.role_label}</span>
                      <span className="dash-row-meta">
                        Role · {role.chosen_at ? `chosen ${shortDate(role.chosen_at)}` : "selected to practise"}
                      </span>
                    </div>
                    <span aria-hidden="true" className="dash-chevron">›</span>
                  </button>
                ))}
                {jobDescriptions === "error" ? (
                  <div className="dash-row dash-row--message">
                    <span>We couldn&rsquo;t load this. Please try again.</span>
                    <button type="button" className="dash-link" onClick={loadJobDescriptions}>Try Again</button>
                  </div>
                ) : jobDescriptions.length === 0 && roleRows.length === 0 ? (
                  <div className="dash-row dash-row--message">
                    <span>No roadmaps yet.</span>
                  </div>
                ) : (
                  jobDescriptions.map((jd) => (
                    <div className="dash-row" key={jd.job_description_id}>
                      <button
                        type="button"
                        className="dash-row-open"
                        onClick={() => {
                          setCurrentJobDescriptionId(jd.job_description_id);
                          navigate("/job-description-comparison");
                        }}
                      >
                        <span className="dash-row-title">{jd.role_title_guess || "Job description"}</span>
                        <span className="dash-row-meta">Job ad you analysed · {shortDate(jd.created_at)}</span>
                      </button>
                      <button
                        type="button"
                        className="dash-remove"
                        onClick={() => { setRemoveError(""); setRemoveTarget(jd); }}
                      >
                        Remove
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </>
        )}
      </div>

      {removeTarget && (
        <div className="atm-overlay" onClick={isRemoving ? undefined : () => setRemoveTarget(null)}>
          <div
            className="atm-modal atm-modal--compact"
            role="dialog"
            aria-modal="true"
            aria-labelledby="dash-remove-title"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="atm-title" id="dash-remove-title">Remove this job description?</h2>
            <p className="atm-subtitle">
              This can&rsquo;t be undone. Your completed activities stay in your practice history.
            </p>
            {removeError && <p className="atm-field-error">{removeError}</p>}
            <div className="atm-actions-row">
              <button type="button" className="atm-btn-outline" onClick={() => setRemoveTarget(null)} disabled={isRemoving}>
                Cancel
              </button>
              <button type="button" className="atm-btn-destructive" onClick={handleRemove} disabled={isRemoving}>
                {isRemoving ? "Removing…" : "Remove"}
              </button>
            </div>
          </div>
        </div>
      )}

      {toast && (
        <div className="dash-toast" role="status">
          <CheckIcon size={12} /> {toast}
        </div>
      )}
    </>
  );
}
