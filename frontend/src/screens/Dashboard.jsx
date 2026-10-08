import { useEffect, useState } from "react";
import "../styles/Dashboard.css";
import "../styles/AccessTokenModal.css";
import TopNav from "../components/TopNav";
import { ArrowRightIcon, CheckIcon } from "../components/icons";
import { api } from "../api.js";
import { navigate } from "../navigate.js";
import { getResumeStep } from "../resumeStep.js";

const ACTIVITY_TYPE_LABELS = {
  multiple_choice: "Multiple Choice",
  written_response: "Written Response",
};

const shortDate = (iso) =>
  new Date(iso).toLocaleDateString("en-AU", { day: "numeric", month: "short" });

/**
 * US 3.4 dashboard ("Your progress"). Everything shown is real: completed
 * activities from GET /practice-sessions/recent-activities and saved job
 * descriptions from GET /job-descriptions (removable, AC 3.5.1).
 *
 * Not shown yet: chosen roles and the "next skill" card (AC 3.4.2). Both
 * come from choosing a role on Your Roadmap, which isn't built yet, so the
 * top card shows AC 3.4.2's own "no roadmap yet" state instead - which is
 * simply true today.
 */
export default function Dashboard() {
  const [isChecking, setIsChecking] = useState(true);
  // Each list loads and fails on its own (AC 3.4.1: "keep the rest of the
  // page available"). null = loading, "error" = failed, array = loaded.
  const [activities, setActivities] = useState(null);
  const [jobDescriptions, setJobDescriptions] = useState(null);
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
          navigate(getResumeStep(profile));
          return;
        }
        setIsChecking(false);
        api.getRecentActivities().then(setActivities).catch(() => setActivities("error"));
        api.listJobDescriptions().then(setJobDescriptions).catch(() => setJobDescriptions("error"));
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

  const isLoading = isChecking || activities === null || jobDescriptions === null;
  const nothingYet =
    Array.isArray(activities) && activities.length === 0 &&
    Array.isArray(jobDescriptions) && jobDescriptions.length === 0;

  return (
    <>
      <TopNav />
      <div className="dash-page">
        <h1 className="dash-heading">Your progress</h1>

        {isLoading && <p className="dash-subheading">&nbsp;</p>}

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

            <div className="dash-card dash-next">
              <div>
                <span className="dash-eyebrow">YOUR NEXT STEP</span>
                <h2 className="dash-next-title">Choose a path to build your roadmap.</h2>
              </div>
              <button type="button" className="dash-btn-primary" onClick={() => navigate("/choose-your-path")}>
                Choose Your Path <ArrowRightIcon size={16} />
              </button>
            </div>

            <div className="dash-columns">
              <div className="dash-card">
                <h2 className="dash-card-title">Recent practice</h2>
                {activities === "error" ? (
                  <div className="dash-row dash-row--message">
                    <span>We couldn&rsquo;t load this. Please try again.</span>
                    <button type="button" className="dash-link" onClick={loadActivities}>Try Again</button>
                  </div>
                ) : activities.length === 0 ? (
                  <div className="dash-row dash-row--message">
                    <span>No completed activities yet.</span>
                  </div>
                ) : (
                  activities.map((activity) => (
                    <div className="dash-row" key={`${activity.title}-${activity.completed_at}`}>
                      <div>
                        <span className="dash-row-title">{activity.title}</span>
                        <span className="dash-row-meta">
                          {ACTIVITY_TYPE_LABELS[activity.activity_type] || activity.activity_type} ·{" "}
                          {shortDate(activity.completed_at)}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>

              <div className="dash-card">
                <h2 className="dash-card-title">Your roadmaps</h2>
                {jobDescriptions === "error" ? (
                  <div className="dash-row dash-row--message">
                    <span>We couldn&rsquo;t load this. Please try again.</span>
                    <button type="button" className="dash-link" onClick={loadJobDescriptions}>Try Again</button>
                  </div>
                ) : jobDescriptions.length === 0 ? (
                  <div className="dash-row dash-row--message">
                    <span>No saved job descriptions yet.</span>
                  </div>
                ) : (
                  jobDescriptions.map((jd) => (
                    <div className="dash-row" key={jd.job_description_id}>
                      <div>
                        <span className="dash-row-title">{jd.role_title_guess || "Job description"}</span>
                        <span className="dash-row-meta">Job ad you analysed · {shortDate(jd.created_at)}</span>
                      </div>
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
