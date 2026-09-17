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
// role-specific, and never carry a real activity (AC 4.3.1 exploration
// flavour only).
const UNIVERSAL_AREAS = ['general_workspace', 'reception']

// Since the AI's real content is one MCQ per (role, difficulty) - not one
// per workplace area - each of the real 27 database roles gets exactly one
// "primary" area: the single relevant, clickable hotspot that opens that
// role's activity. Every other area stays visible but disabled, honestly
// reflecting that there's only one real activity behind this session, not
// several distinct ones per area.
const PRIMARY_AREA_BY_ROLE = {
  blockchain_engineer: 'development_studio',
  business_intelligence_analyst: 'data_analytics_lab',
  computer_and_information_research_scientist: 'development_studio',
  computer_and_information_systems_manager: 'project_delivery_board',
  computer_network_architect: 'network_infrastructure_hub',
  computer_network_support_specialist: 'network_infrastructure_hub',
  computer_programmer: 'development_studio',
  computer_systems_analyst: 'project_delivery_board',
  computer_systems_engineer_architect: 'development_studio',
  computer_user_support_specialist: 'support_desk_operations',
  data_scientist: 'data_analytics_lab',
  data_warehousing_specialist: 'data_analytics_lab',
  database_administrator: 'data_analytics_lab',
  database_architect: 'data_analytics_lab',
  digital_forensics_analyst: 'security_operations_room',
  information_security_analyst: 'security_operations_room',
  information_security_engineer: 'security_operations_room',
  it_project_manager: 'project_delivery_board',
  network_and_systems_administrator: 'network_infrastructure_hub',
  penetration_tester: 'security_operations_room',
  software_developer: 'development_studio',
  software_qa_analyst_tester: 'testing_quality_lab',
  telecommunications_engineering_specialist: 'network_infrastructure_hub',
  video_game_designer: 'development_studio',
  web_administrator: 'network_infrastructure_hub',
  web_and_digital_interface_designer: 'product_collaboration_studio',
  web_developer: 'development_studio',
}

// Returns the set of area ids relevant to a role - the two universal areas,
// plus the role's one primary area (falls back to just the universal areas
// for a role outside the 27 the AI has covered so far).
export function getRelevantAreaIds(roleId) {
  const primary = PRIMARY_AREA_BY_ROLE[roleId]
  return new Set(primary ? [primary, ...UNIVERSAL_AREAS] : UNIVERSAL_AREAS)
}

// The one area id that opens this role's real activity, or null if the
// role isn't in the AI's covered set yet (falls back to general_workspace).
export function getPrimaryAreaId(roleId) {
  return PRIMARY_AREA_BY_ROLE[roleId] || 'general_workspace'
}
