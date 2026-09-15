// Client-side mock standing in for a real backend-generated scenario
// (POST /practice-sessions) ahead of the real AI provider. Field names
// deliberately match the real contract in backend/docs/API-CONTRACT.md
// where they overlap (title, task, skills_used) so swapping this for a
// real API response later is a small change, not a rewrite. `situation`,
// `start_area_id` and `task_detail` are workplace-screen-specific
// (AC 4.3.1-4.3.3), added on top of that same shape.
const SCENARIOS = {
  business_analyst: {
    title: 'Requirements Analysis',
    workplace_area: 'Stakeholder Area',
    task: 'Responding to a changing requirement from a stakeholder and deciding how to clarify and document the change.',
    skills_used: ['Requirements gathering', 'Stakeholder communication', 'Jira', 'Documentation'],
    situation: 'Your stakeholder has noticed a decline in customer engagement and asks you to investigate.',
    start_area_id: 'stakeholder_client_studio',
    task_detail: {
      character_name: 'Priya',
      character_intro: 'She owns the checkout work. Engagement has dropped since the last release and she wants the requirement changed before the next one goes out.',
      what_to_do: 'Decide how to clarify the change and where it should be recorded.',
    },
  },
  data_analyst: {
    title: 'Reporting Deep-Dive',
    workplace_area: 'Analytics Desk',
    task: 'A stakeholder asks why last month’s numbers look off - deciding how to investigate and what to report back.',
    skills_used: ['Data analysis', 'SQL', 'Reporting', 'Stakeholder communication'],
    situation: 'A stakeholder has flagged that last month’s revenue numbers look wrong and wants an explanation before the next meeting.',
    start_area_id: 'data_analytics_lab',
    task_detail: {
      character_name: 'Marcus',
      character_intro: 'He owns the revenue reporting dashboard and needs to know whether the drop is real or a data issue before he presents it.',
      what_to_do: 'Decide how you would investigate the numbers and what you would report back.',
    },
  },
  software_developer: {
    title: 'Slow Responses After a Release',
    workplace_area: 'Engineering Team Desk',
    task: 'Your team shipped an update this morning and customers are reporting slow response times - deciding what to investigate first.',
    skills_used: ['Debugging', 'Communication', 'API design'],
    situation: 'Customers are reporting slow response times right after this morning’s release.',
    start_area_id: 'development_studio',
    task_detail: {
      character_name: 'Sam',
      character_intro: 'He’s on support and is getting complaints about the order history page loading slowly since the release went out.',
      what_to_do: 'Decide what you would investigate first, and why.',
    },
  },
  web_developer: {
    title: 'A Layout Bug on Launch Day',
    workplace_area: 'Front-End Desk',
    task: 'A key page looks broken for some users right after a release - deciding how to reproduce, prioritise and communicate it.',
    skills_used: ['Debugging', 'CSS', 'Cross-browser testing', 'Communication'],
    situation: 'Support is getting reports that the checkout page looks broken for some users since this morning’s release.',
    start_area_id: 'development_studio',
    task_detail: {
      character_name: 'Alex',
      character_intro: 'They handle support tickets and have a growing list of screenshots from confused customers.',
      what_to_do: 'Decide how you would reproduce the issue and what you would prioritise first.',
    },
  },
  web_and_digital_interface_designer: {
    title: 'Conflicting Feedback on a New Flow',
    workplace_area: 'Design Studio',
    task: 'Two stakeholders have given you conflicting feedback on a new checkout flow - deciding how to reconcile it before the deadline.',
    skills_used: ['User research', 'Prototyping', 'Stakeholder communication'],
    situation: 'Two stakeholders have given conflicting feedback on the new checkout flow, and the deadline is this week.',
    start_area_id: 'product_collaboration_studio',
    task_detail: {
      character_name: 'Jordan',
      character_intro: 'They lead product and want the flow simplified, while the support lead wants more confirmation steps to reduce errors.',
      what_to_do: 'Decide how you would reconcile the feedback and move forward.',
    },
  },
  computer_systems_analyst: {
    title: 'A Conflicting System Requirement',
    workplace_area: 'Systems Desk',
    task: 'Two teams have given you conflicting requirements for the same system change - deciding how to reconcile them.',
    skills_used: ['Requirements gathering', 'Documentation', 'Stakeholder communication'],
    situation: 'Two teams have submitted conflicting requirements for the same upcoming system change.',
    start_area_id: 'project_delivery_board',
    task_detail: {
      character_name: 'Dana',
      character_intro: 'She leads one of the two teams and is concerned the other team’s requirement will break her team’s workflow.',
      what_to_do: 'Decide how you would reconcile the two requirements.',
    },
  },
  it_project_manager: {
    title: 'A Slipping Deadline',
    workplace_area: 'Delivery Desk',
    task: 'A key deliverable is at risk of missing its deadline - deciding how to respond and who to inform.',
    skills_used: ['Planning', 'Stakeholder communication', 'Risk management'],
    situation: 'A key deliverable looks like it will miss its deadline, and the client hasn’t been told yet.',
    start_area_id: 'stakeholder_client_studio',
    task_detail: {
      character_name: 'Leo',
      character_intro: 'He leads the delivery team and has just flagged that testing is running two weeks behind schedule.',
      what_to_do: 'Decide how you would respond, and who you would inform first.',
    },
  },
  database_administrator: {
    title: 'A Slow Query in Production',
    workplace_area: 'Database Operations Desk',
    task: 'A report that used to run in seconds is now timing out - deciding how to diagnose and fix it safely.',
    skills_used: ['SQL', 'Performance tuning', 'Documentation'],
    situation: 'A report that used to run in seconds is now timing out in production.',
    start_area_id: 'data_analytics_lab',
    task_detail: {
      character_name: 'Priya',
      character_intro: 'She runs this report every morning for the leadership team and needs it working again before their 9am meeting.',
      what_to_do: 'Decide how you would diagnose and safely fix the slow query.',
    },
  },
  database_architect: {
    title: 'A Schema Change Request',
    workplace_area: 'Architecture Desk',
    task: 'A team wants a schema change that could affect other services - deciding how to evaluate and respond.',
    skills_used: ['Data modelling', 'Documentation', 'Stakeholder communication'],
    situation: 'A team has requested a schema change that could impact two other services sharing the same database.',
    start_area_id: 'development_studio',
    task_detail: {
      character_name: 'Noah',
      character_intro: 'He leads the requesting team and needs an answer today so his team can plan their sprint.',
      what_to_do: 'Decide how you would evaluate the request and respond.',
    },
  },
  data_scientist: {
    title: 'A Model Behaving Unexpectedly',
    workplace_area: 'Analytics Lab',
    task: 'A model’s predictions have shifted noticeably since last week - deciding how to investigate.',
    skills_used: ['Data analysis', 'Model evaluation', 'Communication'],
    situation: 'A model’s predictions have shifted noticeably since last week, and the product team has noticed.',
    start_area_id: 'data_analytics_lab',
    task_detail: {
      character_name: 'Mei',
      character_intro: 'She manages the product relying on this model and wants to know if it can still be trusted.',
      what_to_do: 'Decide how you would investigate the shift before responding to her.',
    },
  },
  information_security_analyst: {
    title: 'An Unusual Login Alert',
    workplace_area: 'Security Operations Desk',
    task: 'A monitoring alert flags an unusual login pattern - deciding how to investigate and who to notify.',
    skills_used: ['Incident response', 'Log analysis', 'Documentation'],
    situation: 'A monitoring alert has flagged an unusual login pattern on a customer-facing account overnight.',
    start_area_id: 'security_operations_room',
    task_detail: {
      character_name: 'Chris',
      character_intro: 'They’re on the overnight shift and escalated this as soon as the pattern looked off.',
      what_to_do: 'Decide how you would investigate the alert and who you would notify.',
    },
  },
  information_security_engineer: {
    title: 'A Vulnerable Dependency',
    workplace_area: 'Security Engineering Desk',
    task: 'A scan has flagged a vulnerable dependency in a live service - deciding how to prioritise the fix.',
    skills_used: ['Vulnerability management', 'Risk assessment', 'Communication'],
    situation: 'An automated scan has flagged a known vulnerability in a dependency used by a live service.',
    start_area_id: 'security_operations_room',
    task_detail: {
      character_name: 'Robin',
      character_intro: 'They lead the affected service team and are asking how urgent this really is.',
      what_to_do: 'Decide how you would prioritise the fix and communicate the risk.',
    },
  },
  computer_network_support_specialist: {
    title: 'An Intermittent Connectivity Issue',
    workplace_area: 'Network Support Desk',
    task: 'A team reports the network keeps dropping for a few seconds at a time - deciding how to narrow down the cause.',
    skills_used: ['Network troubleshooting', 'Documentation', 'Communication'],
    situation: 'A team keeps losing network connectivity for a few seconds at a time, several times a day.',
    start_area_id: 'network_infrastructure_hub',
    task_detail: {
      character_name: 'Tia',
      character_intro: 'She sits with the affected team and says it’s been happening for two days, always around the same time.',
      what_to_do: 'Decide how you would narrow down the cause.',
    },
  },
  network_and_systems_administrator: {
    title: 'An Unexpected Server Restart',
    workplace_area: 'Systems Desk',
    task: 'A production server restarted overnight with no scheduled maintenance - deciding how to investigate.',
    skills_used: ['System administration', 'Log analysis', 'Documentation'],
    situation: 'A production server restarted overnight with no scheduled maintenance on record.',
    start_area_id: 'network_infrastructure_hub',
    task_detail: {
      character_name: 'Omar',
      character_intro: 'He noticed a short outage in the monitoring dashboard this morning and wants to know what happened before it happens again.',
      what_to_do: 'Decide how you would investigate the unexpected restart.',
    },
  },
};

// A reasonable generic scenario for any role without a specific mapping
// above, so every role still gets something concrete to prepare for.
function genericScenario(roleLabel) {
  return {
    title: 'A New Priority Comes In',
    workplace_area: `${roleLabel} Desk`,
    task: `A colleague asks for your help with an unexpected, time-sensitive request - deciding how to prioritise it as a ${roleLabel.toLowerCase()}.`,
    skills_used: ['Communication', 'Prioritisation', 'Problem solving'],
    situation: `A colleague needs your help with an unexpected, time-sensitive request.`,
    start_area_id: 'general_workspace',
    task_detail: {
      character_name: 'A colleague',
      character_intro: 'They’ve just asked for your help with something urgent that wasn’t on today’s plan.',
      what_to_do: 'Decide how you would prioritise this against your existing work.',
    },
  };
}

// Generic task content for a relevant area that isn't the scenario's
// designated "start" area - keeps every relevant hotspot clickable and
// meaningful, without needing hand-written content for all of them yet.
export function getGenericAreaTask(areaLabel) {
  return {
    character_name: 'A colleague',
    character_intro: `Someone in the ${areaLabel} has a question related to your current practice scenario.`,
    what_to_do: 'Explore this area and decide how you would help.',
  };
}

export function getPracticeScenario(roleId, roleLabel) {
  return SCENARIOS[roleId] || genericScenario(roleLabel || 'your role');
}
