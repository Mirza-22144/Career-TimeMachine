import { useEffect, useState } from "react";
import "../styles/ProfileSetUp.css";
import TopNav from "../components/TopNav";
import { CheckIcon } from "../components/icons";
import { api } from "../api.js";
import { navigate } from "../navigate.js";

const yearLabel = (iso) => (iso ? iso.slice(0, 4) : "");

/**
 * "Your career profile is set up." (AC 3.2.4) - shown once, right after
 * the first Save My Profile confirmation, before Choose Your Path. Reads
 * the just-saved profile back from the real backend rather than trusting
 * local wizard state, so the summary always reflects what was actually
 * persisted.
 */
export default function ProfileSetUp() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [summary, setSummary] = useState(null);

  const load = async () => {
    try {
      const [profile, roles, experienceOptions, skills] = await Promise.all([
        api.getProfile(),
        api.getCatalogue("roles"),
        api.getCatalogue("experience-options"),
        api.getCatalogue("skills"),
      ]);

      const roleLabel =
        profile.role_id === "other"
          ? profile.role_other_text
          : roles.find((r) => r.id === profile.role_id)?.label || profile.role_id;
      const yearsLabel = experienceOptions.find((y) => y.id === profile.years_experience)?.label || "";

      const skillLabels = [
        ...profile.skill_ids.map((id) => skills.find((s) => s.id === id)?.label || id),
        ...profile.custom_skills,
      ];
      const responsibilityCount = profile.responsibility_ids.length + profile.custom_responsibilities.length;

      const startYear = yearLabel(profile.break_started_on);
      const returnYear = yearLabel(profile.planned_return_date);
      const durationYears =
        startYear && returnYear ? Number(returnYear) - Number(startYear) : null;

      setSummary({
        story: { value: roleLabel, caption: yearsLabel ? `${yearsLabel} in IT` : "" },
        experience: {
          value: `${skillLabels.length} skills, ${responsibilityCount} responsibilities`,
          caption: skillLabels.join(", "),
        },
        break_: {
          value: profile.return_date_unsure ? `${startYear} onward` : `${startYear} to ${returnYear}`,
          caption:
            durationYears != null
              ? `${durationYears} ${durationYears === 1 ? "year" : "years"} away`
              : "Return date to be decided",
        },
      });
      setLoading(false);
    } catch {
      setLoadError(true);
      setLoading(false);
    }
  };

  useEffect(() => {
    async function run() {
      await load();
    }
    run();
  }, []);

  const retry = () => {
    setLoading(true);
    setLoadError(false);
    load();
  };

  return (
    <>
      <TopNav />
      <div className="psu-page">
        {loading && <div className="psu-content" />}

        {!loading && loadError && (
          <div className="psu-content">
            <p>We couldn&rsquo;t load your profile. Please try again.</p>
            <button type="button" onClick={retry}>
              Try Again
            </button>
          </div>
        )}

        {!loading && !loadError && summary && (
          <div className="psu-content">
            <div className="psu-check">
              <CheckIcon size={20} color="#7C3AED" />
            </div>
            <h1 className="psu-heading">Your career profile is set up.</h1>
            <p className="psu-subheading">Everything below is saved to your access token. Next, choose how you want to continue.</p>

            <div className="psu-rows">
              <div className="psu-row">
                <span className="psu-row-label">YOUR STORY</span>
                <strong className="psu-row-value">{summary.story.value}</strong>
                <span className="psu-row-caption">{summary.story.caption}</span>
              </div>
              <div className="psu-row">
                <span className="psu-row-label">YOUR EXPERIENCE</span>
                <strong className="psu-row-value">{summary.experience.value}</strong>
                <span className="psu-row-caption">{summary.experience.caption}</span>
              </div>
              <div className="psu-row">
                <span className="psu-row-label">YOUR BREAK</span>
                <strong className="psu-row-value">{summary.break_.value}</strong>
                <span className="psu-row-caption">{summary.break_.caption}</span>
              </div>
            </div>
          </div>
        )}

        {!loading && !loadError && (
          <div className="psu-footer">
            <span className="psu-footer-note">You can edit your profile any time from the profile icon.</span>
            <button type="button" className="psu-continue" onClick={() => navigate("/choose-your-path")}>
              Continue <span aria-hidden="true">›</span>
            </button>
          </div>
        )}
      </div>
    </>
  );
}
