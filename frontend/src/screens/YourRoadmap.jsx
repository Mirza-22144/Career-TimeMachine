import { useEffect, useRef, useState } from "react";
import "../styles/YourRoadmap.css";
import TopNav from "../components/TopNav";
import LoadingPopup from "../components/LoadingPopup";
import RoleInfoModal from "../components/RoleInfoModal";
import { ArrowRightIcon, CheckIcon } from "../components/icons";
import { api } from "../api.js";
import { navigate } from "../navigate.js";
import { sendToProfileSetup } from "../resumeStep.js";
import { recallResult, rememberResult } from "../lastGood.js";

const shortDate = (iso) => new Date(iso).toLocaleDateString("en-AU", { day: "numeric", month: "short" });

// "Builds on your SQL and Python" - written from the skills of hers that
// are actually listed for the role, so it is never a claim the data
// doesn't support.
function buildsOn(role) {
  const labels = role.skills_bring_back.slice(0, 2).map((s) => s.label);
  if (labels.length === 0) return "A new direction to explore";
  return `Builds on your ${labels.join(" and ")}`;
}

// How far right of the previous-role card each branch finishes curving.
const CURVE_WIDTH = 150;

// Measures the cards and returns one SVG path per suggested role: a curve
// out of the previous-role card that bends to the branch's level, then
// runs straight through its "already yours" skills into the role's card.
function measureBranches(map) {
  const origin = map.getBoundingClientRect();
  const previous = map.querySelector("[data-previous-card]")?.getBoundingClientRect();
  if (!previous) return null;
  const startX = previous.right - origin.left;
  const startY = previous.top + previous.height / 2 - origin.top;

  const paths = [...map.querySelectorAll("[data-branch]")].map((branch) => {
    const card = branch.querySelector("[data-branch-card]").getBoundingClientRect();
    const anchor = branch.querySelector("[data-branch-anchor]")?.getBoundingClientRect();
    let y = (anchor || card).top + (anchor || card).height / 2;
    y = Math.min(Math.max(y, card.top + 20), card.bottom - 20) - origin.top;
    const bendX = startX + CURVE_WIDTH;
    const endX = card.left - origin.left;
    const half = CURVE_WIDTH / 2;
    return `M ${startX} ${startY} C ${startX + half} ${startY}, ${bendX - half} ${y}, ${bendX} ${y} L ${endX} ${y}`;
  });
  return { startX, startY, paths, width: origin.width, height: origin.height };
}

function OwnedChips({ skills, isAnchor }) {
  return (
    <div className="yr-chips" data-branch-anchor={isAnchor ? "" : undefined}>
      {skills.map((skill) => (
        <span key={skill.label} className="yr-chip yr-chip--owned">
          <CheckIcon size={11} color="#3730a3" /> {skill.label}
        </span>
      ))}
    </div>
  );
}

// Skills You Could Explore. Practised / Next / Later labels only appear
// once she has practised something for this role (AC 2.2.4).
function ExploreChips({ skills, stacked }) {
  const showStatus = skills.some((s) => s.status === "practised");
  return (
    <div className={`yr-chips ${stacked ? "yr-chips--stacked" : ""}`}>
      {skills.map((skill) => (
        <span key={skill.id} className="yr-chip-row">
          {skill.status === "practised" ? (
            <span className="yr-chip yr-chip--owned">
              <CheckIcon size={11} color="#3730a3" /> {skill.label}
            </span>
          ) : (
            <span className="yr-chip yr-chip--explore">+ {skill.label}</span>
          )}
          {showStatus && stacked && (
            <span className={`yr-status yr-status--${skill.status}`}>
              {skill.status === "practised" && `Practised ${shortDate(skill.practised_on)}`}
              {skill.status === "next" && "Next"}
              {skill.status === "later" && "Later"}
            </span>
          )}
        </span>
      ))}
    </div>
  );
}

function PractiseToggle({ isSelected, onSelect }) {
  return (
    <button type="button" className="yr-practise" role="radio" aria-checked={isSelected} onClick={onSelect}>
      <span className={`yr-radio ${isSelected ? "yr-radio--on" : ""}`}>
        {isSelected && <CheckIcon size={10} />}
      </span>
      <span className={isSelected ? "yr-practise-label--on" : ""}>
        {isSelected ? "Selected to practise" : "Practise this role"}
      </span>
    </button>
  );
}

// Your Roadmap (AC 2.2.3 / 2.2.4), reached from Choose Your Path's Explore
// Roles. All data comes from GET /roadmap; only the info panel's
// relationship text is mock (see mockData/roadmapData.js).
export default function YourRoadmap() {
  const [status, setStatus] = useState("loading"); // loading | error | ready
  const [roadmap, setRoadmap] = useState(null);
  const [selectedRoleId, setSelectedRoleId] = useState(null);
  const [saveFailedFor, setSaveFailedFor] = useState(null);
  const [infoRole, setInfoRole] = useState(null);
  const mapRef = useRef(null);
  const [branches, setBranches] = useState(null);
  // True when showing the last roadmap that loaded because a fresh one
  // could not be fetched (AC 3.2.5 exception).
  const [isStale, setIsStale] = useState(false);

  // Redraw the connector curves whenever the map's size changes (first
  // layout, window resize, fonts loading, a status label appearing).
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return undefined;
    const observer = new ResizeObserver(() => setBranches(measureBranches(map)));
    observer.observe(map);
    return () => observer.disconnect();
  }, [status]);

  const load = async () => {
    try {
      const profile = await api.getProfile();
      if (!profile.confirmed) {
        sendToProfileSetup(profile);
        return;
      }
      const data = await api.getRoadmap();
      rememberResult("roadmap", data);
      setRoadmap(data);
      setSelectedRoleId(data.selected_role_id);
      setIsStale(false);
      setStatus("ready");
    } catch {
      const earlier = recallResult("roadmap");
      if (earlier?.previous_role) {
        setRoadmap(earlier);
        setSelectedRoleId(earlier.selected_role_id);
        setIsStale(true);
        setStatus("ready");
      } else {
        setStatus("error");
      }
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

  // "Practise this role" saves straight away, so the choice is on her
  // dashboard even if she leaves without starting practice.
  const selectRole = async (role, source) => {
    setSaveFailedFor(null);
    try {
      await api.putPracticeRole(role.role_id, source);
      setSelectedRoleId(role.role_id);
    } catch {
      setSaveFailedFor({ role, source });
    }
  };

  if (status !== "ready") {
    return (
      <>
        <TopNav />
        <div className="yr-page">
          {status === "loading" && <LoadingPopup text="Opening your roadmap…" />}
          {status === "error" && (
            <div className="yr-message">
              <p>We couldn&rsquo;t open your roadmap. Please try again.</p>
              <button type="button" className="yr-btn-outline" onClick={retry}>Try Again</button>
            </div>
          )}
        </div>
      </>
    );
  }

  const previous = roadmap.previous_role;
  const suggested = roadmap.suggested_roles;
  const allRoles = [previous, ...suggested];
  const selectedRole = allRoles.find((role) => role.role_id === selectedRoleId);

  return (
    <>
      <TopNav />
      <div className="yr-page">
        <span className="yr-eyebrow">EXPLORE ROLES</span>
        <h1 className="yr-heading">Your roadmap</h1>
        <p className="yr-subheading">
          Your experience already leads somewhere. Follow a branch, then select the role you want to practise.
        </p>

        {isStale && (
          <div className="yr-stale" role="status">
            <span>This was based on your earlier profile.</span>
            <button type="button" onClick={retry}>Try Again</button>
          </div>
        )}

        <div className="yr-map" role="radiogroup" aria-label="Role to practise" ref={mapRef}>
          {branches && (
            <svg
              className="yr-connectors"
              width={branches.width}
              height={branches.height}
              viewBox={`0 0 ${branches.width} ${branches.height}`}
              aria-hidden="true"
            >
              {branches.paths.map((d) => <path key={d} d={d} />)}
              {branches.paths.length > 0 && <circle cx={branches.startX} cy={branches.startY} r="5" />}
            </svg>
          )}
          <div
            data-previous-card
            className={`yr-card yr-card--previous ${selectedRoleId === previous.role_id ? "yr-card--selected" : ""}`}
          >
            <div className="yr-card-top">
              <span className="yr-card-label">WHERE YOU HAVE BEEN</span>
              <button type="button" className="yr-info" aria-label={`Information about ${previous.role_label}`} onClick={() => setInfoRole(previous)}>
                i
              </button>
            </div>
            <h2 className="yr-card-title">{previous.role_label}</h2>
            <p className="yr-card-caption">
              {roadmap.years_experience_label ? `${roadmap.years_experience_label} · ` : ""}the role you recorded
            </p>

            <span className="yr-section-label">SKILLS YOU BRING BACK</span>
            <OwnedChips skills={previous.skills_bring_back} />

            {!previous.skill_data_available ? (
              <p className="yr-note">Skill information isn&rsquo;t available for this role yet.</p>
            ) : previous.skills_could_explore.length === 0 ? (
              <p className="yr-note">You already have the skills commonly listed for this role.</p>
            ) : (
              <>
                <span className="yr-section-label yr-section-label--violet">COULD EXPLORE</span>
                <ExploreChips skills={previous.skills_could_explore} stacked />
              </>
            )}

            <PractiseToggle
              isSelected={selectedRoleId === previous.role_id}
              onSelect={() => selectRole(previous, "previous")}
            />
          </div>

          <div className="yr-branches">
            {suggested.length === 0 && (
              <p className="yr-note yr-note--center">
                We couldn&rsquo;t suggest other roles right now. You can continue with your previous role.
              </p>
            )}
            {suggested.map((role) => (
              <div className="yr-branch" key={role.role_id} data-branch>
                <div className="yr-branch-skills">
                  {!role.skill_data_available ? (
                    <p className="yr-note">Skill information isn&rsquo;t available for this role yet.</p>
                  ) : (
                    <>
                      {role.skills_bring_back.length > 0 && (
                        <>
                          <span className="yr-section-label yr-section-label--violet">ALREADY YOURS</span>
                          <OwnedChips skills={role.skills_bring_back} isAnchor />
                        </>
                      )}
                      {role.skills_could_explore.length === 0 ? (
                        <p className="yr-note">You already have the skills commonly listed for this role.</p>
                      ) : (
                        <>
                          <span className="yr-section-label yr-section-label--violet">COULD EXPLORE ON THE WAY</span>
                          <ExploreChips skills={role.skills_could_explore} />
                        </>
                      )}
                    </>
                  )}
                </div>

                <div data-branch-card className={`yr-card ${selectedRoleId === role.role_id ? "yr-card--selected" : ""}`}>
                  <div className="yr-card-top">
                    <span className="yr-card-label yr-card-label--violet">WHERE IT COULD LEAD</span>
                    <button type="button" className="yr-info" aria-label={`Information about ${role.role_label}`} onClick={() => setInfoRole(role)}>
                      i
                    </button>
                  </div>
                  <h2 className="yr-card-title">{role.role_label}</h2>
                  <p className="yr-card-caption">{buildsOn(role)}</p>
                  <PractiseToggle
                    isSelected={selectedRoleId === role.role_id}
                    onSelect={() => selectRole(role, "predicted")}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <p className="yr-source">Skills commonly listed for each role, O*NET</p>

        {saveFailedFor && (
          <div className="yr-save-error" role="alert">
            <span>We couldn&rsquo;t save your choice. Please try again.</span>
            <button type="button" onClick={() => selectRole(saveFailedFor.role, saveFailedFor.source)}>Try Again</button>
          </div>
        )}

        <div className="yr-footer">
          <span className="yr-footer-note">
            {selectedRole
              ? `You will practise as a ${selectedRole.role_label}. You can come back and choose another role.`
              : "Select a role to practise. Use the i on any card for current job vacancies."}
          </span>
          <div className="yr-footer-actions">
            <button type="button" className="yr-btn-outline" onClick={() => window.history.back()}>
              Back
            </button>
            <button
              type="button"
              className="yr-btn-primary"
              disabled={!selectedRole}
              onClick={() => navigate("/workplace-scenario")}
            >
              Start practice <ArrowRightIcon size={16} />
            </button>
          </div>
        </div>
      </div>

      {infoRole && (
        <RoleInfoModal
          role={infoRole}
          isPrevious={infoRole.role_id === previous.role_id}
          previousRoleLabel={previous.role_label}
          onClose={() => setInfoRole(null)}
        />
      )}
    </>
  );
}
