import "../styles/Dashboard.css";
import TopNav from "../components/TopNav";
import { navigate } from "../navigate.js";

/**
 * Placeholder for AC 5.2.1/5.2.2 ("Your map for this job" and the
 * closest-role picker). The comparison itself needs new backend reasoning
 * that doesn't exist yet (matching a profile against extracted
 * requirements into Bring Back / Worth Refreshing / Transferable
 * Experience / Could Explore isn't simple lookup - see
 * ITERATION-3-PROGRESS.md) - this is an honest "coming soon" rather than
 * any placeholder data.
 */
export default function JobDescriptionComparison() {
  return (
    <>
      <TopNav />
      <div className="dash-page dash-page--centered">
        <div className="dash-placeholder">
          <h1 className="dash-title">Comparing your profile is coming soon.</h1>
          <p className="dash-text">
            This is where you&rsquo;ll see how your skills and experience relate to what this job asks for.
          </p>
          <button type="button" className="dash-cta" onClick={() => navigate("/choose-your-path")}>
            Back to Choose Your Path
          </button>
        </div>
      </div>
    </>
  );
}
