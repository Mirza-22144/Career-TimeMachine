import { useEffect, useRef, useState } from "react";
import "../styles/JobDescriptionComparison.css";
import TopNav from "../components/TopNav";
import LoadingPopup from "../components/LoadingPopup";
import ClosestRoleDialog from "../components/ClosestRoleDialog";
import { ArrowRightIcon, RefreshIcon } from "../components/icons";
import { api } from "../api.js";
import { navigate } from "../navigate.js";
import { sendToProfileSetup } from "../resumeStep.js";
import { getCurrentJobDescriptionId } from "../currentJob.js";
import { recallResult, rememberResult } from "../lastGood.js";

/**
 * "Your map for this job" (AC 5.2.1) and the closest-role step (AC 5.2.2).
 * The four groups come from GET /job-descriptions/{id}/comparison, which
 * matches the ad's extracted requirements against her real profile. No
 * score, percentage or verdict is shown anywhere.
 */
// How many of the job's skills fit inside its circle before "+N more".
const MAX_EXPLORE_SHOWN = 8;

// The circles size themselves to what they hold. A column's content has to
// fit within this share of a circle's diameter (a circle is narrower towards
// its top and bottom, so not the whole height is usable). When it doesn't:
// first the map takes the full page width, which makes the circles bigger;
// if that is still not enough, the text inside is set smaller.
const USABLE_SHARE_OF_DIAMETER = 0.7;
const FIT_NORMAL = 0;
const FIT_WIDE = 1;
const FIT_WIDE_AND_COMPACT = 2;

export default function JobDescriptionComparison() {
  const [status, setStatus] = useState("loading"); // loading | error | none | ready
  const [comparison, setComparison] = useState(null);
  const [showAllExplore, setShowAllExplore] = useState(false);
  const [fit, setFit] = useState(FIT_NORMAL);
  const vennRef = useRef(null);

  // Grow the circles when their content needs more room. Measured whenever
  // the map changes size: after the data arrives, when "+N more" is opened,
  // and when the window is resized (which starts again from the normal size).
  useEffect(() => {
    const venn = vennRef.current;
    if (!venn || typeof ResizeObserver === "undefined") return undefined;
    let lastPageWidth = document.documentElement.clientWidth;

    const measure = () => {
      const circle = venn.querySelector(".jdc-circle");
      // On a phone the circles are hidden and the map is a plain list.
      if (!circle || circle.offsetParent === null) return;
      const diameter = circle.getBoundingClientRect().width;
      const tallest = Math.max(
        0,
        ...[...venn.querySelectorAll(".jdc-col")].map((column) => {
          const items = [...column.children];
          if (items.length === 0) return 0;
          return items.at(-1).getBoundingClientRect().bottom - items[0].getBoundingClientRect().top;
        }),
      );
      if (tallest > diameter * USABLE_SHARE_OF_DIAMETER) {
        setFit((level) => Math.min(level + 1, FIT_WIDE_AND_COMPACT));
      }
    };

    const observer = new ResizeObserver(() => {
      const pageWidth = document.documentElement.clientWidth;
      if (Math.abs(pageWidth - lastPageWidth) > 40) {
        lastPageWidth = pageWidth;
        setFit(FIT_NORMAL);
      }
      requestAnimationFrame(measure);
    });
    observer.observe(venn);
    return () => observer.disconnect();
  }, [comparison, showAllExplore]);
  const [profile, setProfile] = useState(null);
  const [roleStep, setRoleStep] = useState(null); // { closest, allRoles } while the picker is open
  const [isOpening, setIsOpening] = useState(false);
  const [openError, setOpenError] = useState("");
  const [isStale, setIsStale] = useState(false); // AC 3.2.5 exception

  const load = async () => {
    try {
      const profileData = await api.getProfile();
      if (!profileData.confirmed) {
        sendToProfileSetup(profileData);
        return;
      }
      // The id handed over by the previous screen, else her most recent one.
      let id = getCurrentJobDescriptionId();
      if (!id) id = (await api.listJobDescriptions())[0]?.job_description_id;
      if (!id) {
        setStatus("none");
        return;
      }
      setProfile(profileData);
      try {
        const fresh = await api.getJobComparison(id);
        rememberResult(`job_map_${id}`, fresh);
        setComparison(fresh);
        setIsStale(false);
      } catch {
        const earlier = recallResult(`job_map_${id}`);
        if (!earlier) throw new Error("no earlier map");
        setComparison(earlier);
        setIsStale(true);
      }
      setStatus("ready");
    } catch {
      setStatus("error");
    }
  };

  useEffect(() => {
    async function run() {
      await load();
    }
    run();
  }, []);

  const retry = () => {
    setStatus("loading");
    load();
  };

  // Remembers the role for this job description (so it isn't asked
  // again), makes it the role to practise - which is what puts it on her
  // roadmap - then opens the roadmap.
  const openRoadmapFor = async (roleId) => {
    setIsOpening(true);
    setOpenError("");
    try {
      await api.setClosestRole(comparison.job_description_id, roleId);
      await api.putPracticeRole(roleId, roleId === profile.role_id ? "previous" : "predicted");
      navigate("/your-roadmap");
    } catch {
      setOpenError("We couldn’t open your roadmap. Please try again.");
      setIsOpening(false);
    }
  };

  // A role already chosen for this job, or an exact title match, needs no
  // question - straight to the roadmap. Otherwise ask which is closest.
  const handleOpenRoadmap = async () => {
    setIsOpening(true);
    setOpenError("");
    try {
      const [closestRoles, roles] = await Promise.all([
        api.getClosestRoles(comparison.job_description_id),
        api.getCatalogue("roles"),
      ]);
      const knownRoleId = closestRoles.chosen_role_id || closestRoles.exact_role_id;
      if (knownRoleId) {
        await openRoadmapFor(knownRoleId);
        return;
      }
      setRoleStep({
        closest: closestRoles.closest,
        allRoles: roles.filter((r) => r.id !== "other").map((r) => ({ role_id: r.id, role_label: r.label })),
      });
      setIsOpening(false);
    } catch {
      setOpenError("We couldn’t open your roadmap. Please try again.");
      setIsOpening(false);
    }
  };

  if (status !== "ready") {
    return (
      <>
        <TopNav />
        <div className="jdc-page">
          {status === "loading" && <LoadingPopup text="Comparing with your profile…" />}
          {status === "error" && (
            <div className="jdc-message">
              <p>We couldn&rsquo;t complete the comparison. Please try again.</p>
              <button type="button" className="jdc-btn-outline" onClick={retry}>Try Again</button>
            </div>
          )}
          {status === "none" && (
            <div className="jdc-message">
              <p>You haven&rsquo;t analysed a job description yet.</p>
              <button type="button" className="jdc-btn-outline" onClick={() => navigate("/analyse-job-description")}>
                Analyse a job description
              </button>
            </div>
          )}
        </div>
      </>
    );
  }

  const { skills_bring_back: bringBack, worth_refreshing: refreshing } = comparison;
  const { transferable_experience: transferable, skills_could_explore: explore } = comparison;

  return (
    <>
      <TopNav />
      <div className="jdc-page">
        <span className="jdc-eyebrow">YOUR MAP FOR THIS JOB · FROM THE JOB DESCRIPTION YOU PASTED</span>
        <h1 className="jdc-heading">{comparison.job_title || "This role"}</h1>
        {comparison.experience_sentence && <p className="jdc-subheading">{comparison.experience_sentence}</p>}

        {isStale && (
          <div className="jdc-stale" role="status">
            <span>This was based on your earlier profile.</span>
            <button type="button" onClick={retry}>Try Again</button>
          </div>
        )}

        <div className={`jdc-layout ${fit >= FIT_WIDE ? "jdc-layout--wide" : ""}`}>
          <div className={`jdc-venn ${fit >= FIT_WIDE_AND_COMPACT ? "jdc-venn--compact" : ""}`} ref={vennRef}>
            <div className="jdc-circle jdc-circle--profile" aria-hidden="true" />
            <div className="jdc-circle jdc-circle--job" aria-hidden="true" />
            <span className="jdc-tag jdc-tag--profile">YOUR PROFILE</span>
            <span className="jdc-tag jdc-tag--job">WHAT THIS JOB ASKS FOR</span>

            <div className="jdc-col">
              <h2 className="jdc-group jdc-group--blue">Transferable Experience</h2>
              {transferable.length === 0 && <p className="jdc-empty">Nothing here for this ad.</p>}
              {transferable.map((item) => (
                <div key={item.experience} className="jdc-transfer">
                  <span className="jdc-chip">{item.experience}</span>
                  <span className="jdc-caption">{item.explanation}</span>
                </div>
              ))}
            </div>

            <div className="jdc-col">
              <h2 className="jdc-group">Skills You Bring Back</h2>
              {bringBack.length === 0 && <p className="jdc-empty">Nothing here for this ad.</p>}
              <div className="jdc-chips">
                {bringBack.map((skill) => <span key={skill} className="jdc-chip">{skill}</span>)}
              </div>
              {bringBack.length > 0 && comparison.break_start_year && (
                <span className="jdc-caption">Last used before your break in {comparison.break_start_year}</span>
              )}
              {refreshing.length > 0 && (
                <>
                  <h2 className="jdc-group jdc-group--spaced">Worth Refreshing</h2>
                  <div className="jdc-chips">
                    {refreshing.map((item) => (
                      <span key={item.requirement} className="jdc-chip" title={`You listed ${item.profile_skill}`}>
                        <RefreshIcon size={13} color="#4338ca" /> {item.requirement}
                      </span>
                    ))}
                  </div>
                </>
              )}
            </div>

            <div className="jdc-col">
              <h2 className="jdc-group">Skills You Could Explore</h2>
              {explore.length === 0 && <p className="jdc-empty">Nothing here for this ad.</p>}
              <div className="jdc-chips jdc-chips--stacked">
                {(showAllExplore ? explore : explore.slice(0, MAX_EXPLORE_SHOWN)).map((skill) => (
                  <span key={skill} className="jdc-chip jdc-chip--explore">{skill}</span>
                ))}
                {explore.length > MAX_EXPLORE_SHOWN && (
                  <button
                    type="button"
                    className="jdc-more"
                    onClick={() => {
                      // Fewer chips may fit the normal size again.
                      setFit(FIT_NORMAL);
                      setShowAllExplore((v) => !v);
                    }}
                  >
                    {showAllExplore ? "Show fewer" : `+${explore.length - MAX_EXPLORE_SHOWN} more`}
                  </button>
                )}
              </div>
            </div>
          </div>

          <aside className="jdc-legend">
            <span className="jdc-legend-label">READING YOUR MAP</span>
            <div className="jdc-legend-item">
              <strong><span className="jdc-dot" /> Where the circles meet</strong>
              <p>Skills in your profile that this ad asks for. Some are marked as worth refreshing.</p>
            </div>
            <div className="jdc-legend-item">
              <strong><span className="jdc-dot" /> Your side</strong>
              <p>Experience of yours that relates to something the ad asks for.</p>
            </div>
            <div className="jdc-legend-item">
              <strong><span className="jdc-dot jdc-dot--dashed" /> The job&rsquo;s side</strong>
              <p>Asked for in the ad and not in your profile yet. Worth exploring, not a gap.</p>
            </div>
          </aside>
        </div>

        {openError && !roleStep && <p className="jdc-error">{openError}</p>}

        <div className="jdc-footer">
          <span className="jdc-footer-note">Next: open the roadmap for the role closest to this job.</span>
          <div className="jdc-footer-actions">
            <button type="button" className="jdc-btn-outline" onClick={() => window.history.back()}>Back</button>
            <button type="button" className="jdc-btn-primary" onClick={handleOpenRoadmap} disabled={isOpening}>
              Open Your Roadmap <ArrowRightIcon size={16} />
            </button>
          </div>
        </div>
      </div>

      {roleStep && (
        <ClosestRoleDialog
          closest={roleStep.closest}
          allRoles={roleStep.allRoles}
          isSaving={isOpening}
          error={openError}
          onConfirm={openRoadmapFor}
          onBack={() => { setRoleStep(null); setOpenError(""); }}
          onExploreRoles={() => navigate("/your-roadmap")}
        />
      )}
    </>
  );
}
