// MOCK DATA for Your Roadmap (screens/YourRoadmap.jsx). Everything else on
// that screen is real; these two pieces are placeholders until a real
// source exists (team decision, 2026-10-08):
//
//  - "Outlook to 2035": no outlook data is loaded yet. Jobs and Skills
//    Australia's Employment Projections is the intended source.
//  - "How it relates to <previous role>": the role-prediction model returns
//    only a role, with no reasoning.
//
// Replace both with backend fields when they exist, then delete this file.

export const MOCK_OUTLOOK_SOURCE = "Source: Jobs and Skills Australia, Employment Projections. Published 2025.";

export function mockOutlook(roleLabel) {
  return `Demand for ${roleLabel} roles is projected to keep growing to 2035, as more services move online and need people to build and maintain them.`;
}

export function mockRelation(roleLabel, previousRoleLabel) {
  return `Much of what you did as a ${previousRoleLabel} carries over to ${roleLabel} work. The skills you already have are commonly listed for this role, so you would be building on familiar ground.`;
}
