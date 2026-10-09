import { useEffect, useState } from "react";
import "../styles/ChooseYourPath.css";
import TopNav from "../components/TopNav";
import LoadingPopup from "../components/LoadingPopup";
import { FileTextIcon, SearchIcon } from "../components/icons";
import { api } from "../api.js";
import { navigate } from "../navigate.js";
import { sendToProfileSetup } from "../resumeStep.js";

/**
 * AC 2.3.3: the fork point right after profile setup (and reachable again
 * later from the dashboard). Replaces the retired Your Direction page -
 * two equally-weighted options, neither preselected or marked recommended.
 *
 * Guards on a confirmed profile itself (not just the nav click that leads
 * here), same reasoning as every other profile-dependent screen - reaching
 * this page by any other route (a bookmark, browser back) with an
 * unconfirmed profile sends her back into the wizard at the first
 * unfinished step, rather than showing a fork into content that assumes a
 * profile which doesn't exist yet.
 */
export default function ChooseYourPath() {
  const [isChecking, setIsChecking] = useState(true);

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
      })
      .catch(() => {
        if (!cancelled) navigate("/your-story");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (isChecking) {
    return (
      <>
        <TopNav />
        <div className="cyp-page"><LoadingPopup text="Opening your paths…" /></div>
      </>
    );
  }

  return (
    <>
      <TopNav />
      <div className="cyp-page">
        <h1 className="cyp-heading">Choose your path</h1>
        <p className="cyp-subheading">
          Two ways to see where your experience fits. You can come back and take the other one at any time.
        </p>

        <div className="cyp-cards">
          <div className="cyp-card">
            <div className="cyp-card-icon">
              <FileTextIcon size={20} />
            </div>
            <h2 className="cyp-card-title">Analyse a Job Description</h2>
            <p className="cyp-card-text">
              Paste a job ad you&rsquo;ve found and see how your experience relates to it.
            </p>
            <button
              type="button"
              className="cyp-card-cta"
              onClick={() => navigate("/analyse-job-description")}
            >
              Analyse a job description <span aria-hidden="true">›</span>
            </button>
          </div>

          <div className="cyp-card">
            <div className="cyp-card-icon">
              <SearchIcon size={20} color="#7C3AED" />
            </div>
            <h2 className="cyp-card-title">Explore Roles</h2>
            <p className="cyp-card-text">
              See where your experience could lead, with current job vacancies for each role.
            </p>
            <button type="button" className="cyp-card-cta" onClick={() => navigate("/your-roadmap")}>
              Explore roles <span aria-hidden="true">›</span>
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
