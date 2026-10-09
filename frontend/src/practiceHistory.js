// Completed Code Review activities, and which activity is unlocked next,
// kept in this browser.
//
// TEMPORARY: Code Review is still mock content (see
// mockData/practiceSession.js) because the AI team has not delivered it,
// so the backend has nowhere to store it yet. Multiple Choice and Drag and
// Drop are real and live in the backend - nothing about them is kept here.
// This is keyed by access token, so it survives a refresh but NOT another
// browser or device. Remove this file when the backend serves Code Review.
import { api } from "./api.js";

const VIEWING_KEY = "ctm_viewing_feedback";

const storageKey = () => `ctm_practice_${api.getToken() || "none"}`;

function readAll() {
  try {
    const data = JSON.parse(localStorage.getItem(storageKey())) || {};
    return { completed: data.completed || [], pending: data.pending || null };
  } catch {
    return { completed: [], pending: null };
  }
}

function writeAll(data) {
  try {
    localStorage.setItem(storageKey(), JSON.stringify(data));
  } catch {
    // Storage blocked or full - practice still works, it just isn't kept.
  }
}

const read = () => readAll().completed;

// The activity unlocked after the last soft stop and not started yet:
// { roleId, difficulty, kind }. It waits for her next visit. A started
// multiple-choice activity is not kept here - the backend holds it.
export function getPending(roleId) {
  const { pending } = readAll();
  return pending && pending.roleId === roleId ? pending : null;
}

export function setPending(pending) {
  writeAll({ ...readAll(), pending });
}

export function clearPending() {
  writeAll({ ...readAll(), pending: null });
}

// One finished activity with her answer, so its feedback can be re-read.
export function addCompleted(entry) {
  const id = `${entry.roleId}:${entry.difficulty}:${entry.activityId}`;
  const completed = read().filter((item) => item.id !== id);
  completed.unshift({ ...entry, id, completedAt: new Date().toISOString() });
  writeAll({ ...readAll(), completed });
}

// Newest first.
export function listCompleted() {
  return read();
}

export function hasCompleted(roleId, difficulty, activityId) {
  return read().some((c) => c.roleId === roleId && c.difficulty === difficulty && c.activityId === activityId);
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

export function getViewingFeedbackId() {
  try {
    return sessionStorage.getItem(VIEWING_KEY);
  } catch {
    return null;
  }
}

export function getLocalFeedback(id) {
  return read().find((item) => item.id === id) || null;
}
