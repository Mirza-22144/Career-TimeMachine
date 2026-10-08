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

// Dashboard "View feedback" ids for questions stored by the backend.
export const apiFeedbackId = (sessionId, scenarioId) => `api:${sessionId}:${scenarioId}`;

export function parseApiFeedbackId(id) {
  if (!id || !id.startsWith("api:")) return null;
  const [, sessionId, ...rest] = id.split(":");
  return { sessionId, scenarioId: rest.join(":") };
}
