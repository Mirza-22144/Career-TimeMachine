// Practice progress and history, kept in this browser.
//
// TEMPORARY (2026-10-08): workplace practice is frontend-only until the
// backend can serve and store the new activity types. Until then this is
// what makes "your place is saved", the dashboard's Recent practice, View
// feedback and "you've completed all the activities" work. It is keyed by
// access token, so it survives a refresh but NOT another browser or
// device, and Clear My Journey does not reach it on other devices.
// Replace every function here with API calls when the backend is ready.
import { api } from "./api.js";

const VIEWING_KEY = "ctm_viewing_feedback";

const storageKey = () => `ctm_practice_${api.getToken() || "none"}`;

function read() {
  try {
    return JSON.parse(localStorage.getItem(storageKey())) || { completed: [], progress: null };
  } catch {
    return { completed: [], progress: null };
  }
}

function write(data) {
  try {
    localStorage.setItem(storageKey(), JSON.stringify(data));
  } catch {
    // Storage blocked or full - practice still works, it just isn't kept.
  }
}

// The session she is part-way through: { roleId, difficulty, currentIndex, answers }.
export function loadProgress(roleId) {
  const { progress } = read();
  return progress && progress.roleId === roleId ? progress : null;
}

export function saveProgress(progress) {
  write({ ...read(), progress });
}

export function clearProgress() {
  write({ ...read(), progress: null });
}

// One finished activity with her answer, so its feedback can be re-read.
export function addCompleted(entry) {
  const data = read();
  const id = `${entry.roleId}:${entry.difficulty}:${entry.activityId}`;
  const completed = data.completed.filter((item) => item.id !== id);
  completed.unshift({ ...entry, id, completedAt: new Date().toISOString() });
  write({ ...data, completed });
}

// Newest first.
export function listCompleted() {
  return read().completed;
}

// True once every activity available for this role and difficulty is done.
export function isExhausted(roleId, difficulty, activityIds) {
  const done = new Set(
    read().completed.filter((c) => c.roleId === roleId && c.difficulty === difficulty).map((c) => c.activityId),
  );
  return activityIds.length > 0 && activityIds.every((id) => done.has(id));
}

export function clearPracticeHistory() {
  try {
    localStorage.removeItem(storageKey());
  } catch {
    // Nothing to clear.
  }
}

// Which completed activity the feedback screen should show - handed over
// like currentJob.js, since the hash router has no URL parameters.
export function setViewingFeedback(id) {
  try {
    sessionStorage.setItem(VIEWING_KEY, id);
  } catch {
    // The feedback screen then shows its "nothing to show" state.
  }
}

export function getViewingFeedback() {
  try {
    const id = sessionStorage.getItem(VIEWING_KEY);
    return read().completed.find((item) => item.id === id) || null;
  } catch {
    return null;
  }
}
