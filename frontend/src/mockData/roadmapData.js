// MOCK DATA for the role information panel (components/RoleInfoModal.jsx).
// Everything else on Your Roadmap is real; this one paragraph is a
// placeholder (team decision, 2026-10-08) because the role-prediction model
// returns only a role, with no reasoning. Replace it with a backend field
// when one exists, then delete this file.

export function mockRelation(roleLabel, previousRoleLabel) {
  return `Much of what you did as a ${previousRoleLabel} carries over to ${roleLabel} work. The skills you already have are commonly listed for this role, so you would be building on familiar ground.`;
}
