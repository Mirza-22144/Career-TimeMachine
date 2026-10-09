// Turns a scenario from the practice API into the shape the practice
// components render (components/practice/ChoiceActivity.jsx and
// PracticeFeedback.jsx), so the real questions and the remaining mock
// activities share one set of screens.
export function toChoiceActivity(scenario) {
  return {
    id: scenario.scenario_id,
    type: "multiple_choice",
    title: scenario.title,
    situation: scenario.situation,
    prompt: scenario.task,
    hint: scenario.guidance,
    options: scenario.options.map((option) => ({ id: option.option_id, text: option.text })),
    skillsUsed: scenario.skills_used,
  };
}

// A drag and drop scenario: the message template "… {blank_1} … {blank_2} …"
// becomes text parts and numbered gaps in reading order. blankIds says which
// backend blank each gap is, so her placements can be sent back by blank id.
export function toDragDropActivity(scenario) {
  const blankIds = [];
  const message = scenario.sentence_template
    .split(/(\{blank_[1-3]\})/)
    .filter((part) => part !== "")
    .map((part) => {
      const match = part.match(/^\{(blank_[1-3])\}$/);
      if (!match) return part.trim();
      blankIds.push(match[1]);
      return { gap: blankIds.length - 1 };
    })
    .filter((part) => part !== "");
  return {
    id: scenario.scenario_id,
    type: "drag_and_drop",
    title: scenario.title,
    situation: scenario.situation,
    instruction: scenario.task,
    message,
    blankIds,
    phrases: scenario.options.map((option) => ({ id: option.option_id, text: option.text })),
    hint: scenario.guidance,
    skillsUsed: scenario.skills_used,
  };
}

// Her submitted message and how each phrase comes across, in the order of
// the gaps as she read them. Null until she has submitted.
export function toDragDropFeedback(scenario, activity) {
  if (!scenario.phrase_feedback) return null;
  const byBlank = Object.fromEntries(scenario.phrase_feedback.map((phrase) => [phrase.blank_id, phrase]));
  return {
    message: scenario.completed_message,
    phrases: activity.blankIds.map((blankId) => ({
      id: byBlank[blankId].option_id,
      text: byBlank[blankId].text,
      comesAcross: byBlank[blankId].comes_across,
      better: byBlank[blankId].what_would_work_better,
    })),
  };
}

// Dashboard "View feedback" ids for questions stored by the backend.
export const apiFeedbackId = (sessionId, scenarioId) => `api:${sessionId}:${scenarioId}`;

export function parseApiFeedbackId(id) {
  if (!id || !id.startsWith("api:")) return null;
  const [, sessionId, ...rest] = id.split(":");
  return { sessionId, scenarioId: rest.join(":") };
}
