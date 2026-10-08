import "../styles/Dashboard.css";
import TopNav from "../components/TopNav";

/**
 * Placeholder for US 3.4's dashboard. The nav item and gating (AC 3.1.6/
 * 3.3.3) are real and live now; the dashboard's own content (completed
 * activities, saved job descriptions, chosen roles, next-skill resume
 * card) is a separate, not-yet-built story - this shows an honest
 * "coming soon" state rather than any placeholder data.
 */
export default function Dashboard() {
  return (
    <>
      <TopNav />
      <div className="dash-page">
        <div className="dash-card">
          <h1 className="dash-title">Your dashboard is coming soon.</h1>
          <p className="dash-text">
            This is where you&rsquo;ll see your completed activities, saved job descriptions and chosen roles.
          </p>
        </div>
      </div>
    </>
  );
}
