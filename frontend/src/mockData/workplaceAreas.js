// The 12 interactive hotspots overlaid on assets/workplace.png (AC 4.3.1).
// `left`/`top` are percentages of the IMAGE itself (not the page), so pins
// stay correctly placed at any screen width. Positions are estimated from
// the approved Figma mock - may need small visual tweaks once seen live.
export const WORKPLACE_AREAS = [
  { id: 'stakeholder_client_studio', label: 'Stakeholder / Client Studio', icon: 'user', left: 9.2, top: 17.2 },
  { id: 'data_analytics_lab', label: 'Data & Analytics Lab', icon: 'barChart', left: 26, top: 23.7 },
  { id: 'dashboard_analytics', label: 'Dashboard / Analytics', icon: 'barChart', left: 6.3, top: 39.3 },
  { id: 'support_desk_operations', label: 'Support Desk / Operations', icon: 'headset', left: 7, top: 76.3 },
  { id: 'project_delivery_board', label: 'Project & Delivery Board', icon: 'fileText', left: 46.4, top: 11.7 },
  { id: 'product_collaboration_studio', label: 'Product / Collaboration Studio', icon: 'lightbulb', left: 69, top: 21.9 },
  { id: 'general_workspace', label: 'General Workspace', icon: 'users', left: 47.8, top: 33.5 },
  { id: 'testing_quality_lab', label: 'Testing & Quality Lab', icon: 'flask', left: 74.4, top: 39.6 },
  { id: 'development_studio', label: 'Development Studio', icon: 'code', left: 89.5, top: 17.7 },
  { id: 'security_operations_room', label: 'Security Operations Room', icon: 'shield', left: 91.7, top: 47 },
  { id: 'network_infrastructure_hub', label: 'Network & Infrastructure Hub', icon: 'globe', left: 88, top: 74.4 },
  { id: 'reception', label: 'Reception', icon: 'bell', left: 47.1, top: 83.1 },
]

// Every role gets these two, regardless of specialisation - they're not
// role-specific areas.
const UNIVERSAL_AREAS = ['general_workspace', 'reception']

// Which areas are relevant to each role (AC 4.3.1: "visually distinguish
// relevant areas from non-relevant areas" - the Figma mock shows every
// area as selectable, but that's a sample; the real screen only lights up
// and allows clicking the areas that make sense for the selected role).
const ROLE_AREAS = {
  business_analyst: ['stakeholder_client_studio', 'data_analytics_lab', 'project_delivery_board', 'product_collaboration_studio'],
  data_analyst: ['data_analytics_lab', 'dashboard_analytics'],
  software_developer: ['development_studio', 'testing_quality_lab', 'project_delivery_board'],
  web_developer: ['development_studio', 'product_collaboration_studio', 'testing_quality_lab'],
  web_and_digital_interface_designer: ['product_collaboration_studio', 'development_studio'],
  computer_systems_analyst: ['project_delivery_board', 'stakeholder_client_studio', 'dashboard_analytics'],
  it_project_manager: ['project_delivery_board', 'stakeholder_client_studio', 'product_collaboration_studio'],
  database_administrator: ['data_analytics_lab', 'network_infrastructure_hub', 'dashboard_analytics'],
  database_architect: ['data_analytics_lab', 'development_studio', 'network_infrastructure_hub'],
  data_scientist: ['data_analytics_lab', 'dashboard_analytics', 'development_studio'],
  information_security_analyst: ['security_operations_room', 'network_infrastructure_hub', 'support_desk_operations'],
  information_security_engineer: ['security_operations_room', 'network_infrastructure_hub', 'development_studio'],
  computer_network_support_specialist: ['network_infrastructure_hub', 'support_desk_operations', 'security_operations_room'],
  network_and_systems_administrator: ['network_infrastructure_hub', 'security_operations_room', 'support_desk_operations'],
}

// Returns the set of area ids relevant to a role - always includes the two
// universal areas, plus whatever role-specific ones are mapped. Unmapped
// roles still get the universal areas, so there's always something to
// click rather than a fully disabled workplace.
export function getRelevantAreaIds(roleId) {
  return new Set([...(ROLE_AREAS[roleId] || []), ...UNIVERSAL_AREAS])
}

// Just the role-specific areas (no general_workspace/reception) - each one
// of these is a real practice activity for the session (AC 4.4.1). The
// universal areas stay clickable/relevant for exploration but don't carry
// their own graded activity.
export function getRoleAreaIds(roleId) {
  return ROLE_AREAS[roleId] || []
}
