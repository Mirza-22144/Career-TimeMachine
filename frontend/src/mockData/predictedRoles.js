// Client-side mock for the AI role-prediction feature (AC 4.1.1) ahead of
// the real internal RoBERTa classifier. Keyed by the real `role` catalogue
// id (from the previous-role step), each entry lists 0-2 plausible "future
// role" suggestions with a short reason. Swap `getPredictedRoles` for a
// real backend/model call once the classifier exists - callers should only
// need to change what's inside this function.
const PREDICTED_ROLES = {
  software_developer: [
    {
      id: "business_intelligence_analyst",
      label: "Business Intelligence Analyst",
      description: "Builds on your requirements, stakeholder and delivery work.",
    },
    {
      id: "data_warehousing_specialist",
      label: "Data Warehousing Specialist",
      description: "Builds on the reporting and analysis you already did.",
    },
  ],
  web_developer: [
    {
      id: "web_and_digital_interface_designer",
      label: "Digital Interface Designer",
      description: "Builds on the interface and user-facing work you already did.",
    },
    {
      id: "business_intelligence_analyst",
      label: "Business Intelligence Analyst",
      description: "Builds on the client and stakeholder work behind your projects.",
    },
  ],
  computer_systems_analyst: [
    {
      id: "it_project_manager",
      label: "IT Project Manager",
      description: "Builds on the planning and cross-team coordination you already did.",
    },
    {
      id: "business_intelligence_analyst",
      label: "Business Intelligence Analyst",
      description: "Builds on the requirements work behind every systems project.",
    },
  ],
  database_administrator: [
    {
      id: "data_scientist",
      label: "Data Scientist",
      description: "Builds on the data structures and querying you already know.",
    },
    {
      id: "database_architect",
      label: "Database Architect",
      description: "Builds on your hands-on database experience at a design level.",
    },
  ],
  information_security_analyst: [
    {
      id: "information_security_engineer",
      label: "Information Security Engineer",
      description: "Builds on the monitoring and response work you already did.",
    },
  ],
  computer_network_support_specialist: [
    {
      id: "network_and_systems_administrator",
      label: "Network and Systems Administrator",
      description: "Builds on the infrastructure support work you already did.",
    },
  ],
};

// Returns the predicted roles for a previous-role id, or an empty list if
// there is no mapping yet - a real, reachable case (AC 4.1.1's "no
// predicted roles available" exception), not just a placeholder for one.
export function getPredictedRoles(roleId) {
  return PREDICTED_ROLES[roleId] || [];
}
