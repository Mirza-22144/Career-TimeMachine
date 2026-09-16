// Client-side mock standing in for a real backend-generated practice
// session (POST /practice-sessions) ahead of the real AI provider. Field
// names deliberately match the real contract in backend/docs/API-CONTRACT.md
// where they overlap (title, task, skills_used) so swapping this for a real
// API response later is a small change, not a rewrite.
//
// A session has one `situation` (the banner shown above the workplace) and
// one activity per role-specific relevant workplace area (see
// mockData/workplaceAreas.js ROLE_AREAS) - not one shared activity for the
// whole session. Each activity has its own pre-activity task_detail (the
// popup shown when the area is clicked), its own MCQ, and its own
// reflective feedback (AC 4.4.1, 4.4.2, 4.5.1, 4.5.2).

function activity(areaId, title, taskDetail, mcq, feedback) {
  return { area_id: areaId, title, task_detail: taskDetail, mcq, feedback }
}

const SESSIONS = {
  business_analyst: {
    focus: 'Requirements Analysis',
    situation: 'Your stakeholder has noticed a decline in customer engagement and asks you to investigate.',
    skills_used: ['Requirements gathering', 'Stakeholder communication', 'Jira', 'Documentation'],
    activities: [
      activity(
        'stakeholder_client_studio',
        'Requirement Clarification',
        {
          character_name: 'Priya',
          character_intro: 'She owns the checkout work. Engagement has dropped since the last release and she wants the requirement changed before the next one goes out.',
          what_to_do: 'Decide how to clarify the change and where it should be recorded.',
        },
        {
          question: 'Priya wants the checkout requirement changed before the next release. The developers are waiting on a decision. What do you do first?',
          options: [
            { id: 'a', text: 'Ask Priya what problem the change is meant to solve, then write it down.' },
            { id: 'b', text: 'Update the requirement document with her wording and tell the developers.' },
            { id: 'c', text: 'Ask the developers to estimate the change before anything is agreed.' },
          ],
          hint: 'A change everyone agrees to verbally is still not a change anyone can test.',
        },
        {
          worked_well: 'You clarified the stakeholder’s concern before proposing a change, so the team is not building against a guess.',
          consider: 'You could also confirm how the change affects the current acceptance criteria before it reaches testing.',
          skill: { title: 'Requirements traceability', text: 'Linking a change back to the requirement it came from is how teams keep track of why something was built.' },
        },
      ),
      activity(
        'data_analytics_lab',
        'Investigating the Drop',
        {
          character_name: 'Marcus',
          character_intro: 'He pulled last week’s engagement numbers and the drop lines up with the last release, but he isn’t sure it’s the cause.',
          what_to_do: 'Decide what you would check before concluding the release caused the drop.',
        },
        {
          question: 'Engagement dropped the same week as the release. What would you check before telling Priya the release is the cause?',
          options: [
            { id: 'a', text: 'Compare the drop against other changes that shipped that week, not just the one release.' },
            { id: 'b', text: 'Tell Priya it’s the release, since the timing lines up.' },
            { id: 'c', text: 'Wait another week to see if engagement recovers on its own.' },
          ],
          hint: 'Two things happening in the same week doesn’t mean one caused the other.',
        },
        {
          worked_well: 'You looked for other explanations before treating the timing as proof.',
          consider: 'It’s also worth checking whether the drop affects all users or just one segment - that narrows down the cause faster.',
          skill: { title: 'Correlation vs. causation', text: 'Two events lining up in time is a reason to investigate further, not a conclusion on its own.' },
        },
      ),
      activity(
        'project_delivery_board',
        'Prioritising the Fix',
        {
          character_name: 'Farah',
          character_intro: 'She runs the delivery board and needs to know where this fix sits against everything else already planned for this sprint.',
          what_to_do: 'Decide how you would position this against the team’s existing priorities.',
        },
        {
          question: 'The requirement change is confirmed, but the sprint is already full. What do you do?',
          options: [
            { id: 'a', text: 'Bring it to Farah with the impact on engagement, and let her weigh it against the current sprint.' },
            { id: 'b', text: 'Quietly ask a developer to squeeze it in without changing the board.' },
            { id: 'c', text: 'Tell Priya it will have to wait until next sprint, without discussing it further.' },
          ],
          hint: 'The board only stays useful if it reflects what the team is actually doing.',
        },
        {
          worked_well: 'You brought the trade-off to the person who owns the board, with the context she needs to decide.',
          consider: 'Naming what would slip if this gets prioritised helps her make a faster, clearer call.',
          skill: { title: 'Prioritisation trade-offs', text: 'Every new priority displaces something else - naming what, explicitly, is what makes prioritisation a decision rather than a guess.' },
        },
      ),
    ],
  },

  data_analyst: {
    focus: 'Data & Reporting Analysis',
    situation: 'A stakeholder has flagged that last month’s revenue numbers look wrong and wants an explanation before the next meeting.',
    skills_used: ['Data analysis', 'SQL', 'Reporting', 'Stakeholder communication'],
    activities: [
      activity(
        'data_analytics_lab',
        'Reporting Deep-Dive',
        {
          character_name: 'Marcus',
          character_intro: 'He owns the revenue reporting dashboard and needs to know whether the drop is real or a data issue before he presents it.',
          what_to_do: 'Decide how you would investigate the numbers and what you would report back.',
        },
        {
          question: 'Last month’s revenue looks lower than expected. What do you check first?',
          options: [
            { id: 'a', text: 'Check whether the drop appears in the raw source data, or only in the dashboard.' },
            { id: 'b', text: 'Recalculate the dashboard formula in case it’s wrong.' },
            { id: 'c', text: 'Tell Marcus the numbers are correct, since the dashboard hasn’t changed.' },
          ],
          hint: 'A wrong number can come from the data, the pipeline, or the dashboard - each needs a different fix.',
        },
        {
          worked_well: 'You isolated whether the issue was in the source data before touching the dashboard logic.',
          consider: 'Checking whether the drop is company-wide or limited to one product line would narrow it down further.',
          skill: { title: 'Root-cause isolation', text: 'Narrowing down where a number goes wrong, before fixing anything, avoids fixing the wrong layer of the pipeline.' },
        },
      ),
      activity(
        'dashboard_analytics',
        'Explaining It to Leadership',
        {
          character_name: 'Sana',
          character_intro: 'She presents the monthly numbers to leadership tomorrow and needs a clear explanation, not just a corrected number.',
          what_to_do: 'Decide what you would include in the explanation.',
        },
        {
          question: 'You’ve found the cause of the drop. How do you prepare Sana for tomorrow’s meeting?',
          options: [
            { id: 'a', text: 'Give her the cause, the corrected number, and what you’d watch for next month.' },
            { id: 'b', text: 'Just give her the corrected number so the meeting can move on.' },
            { id: 'c', text: 'Let her know the number changed, without explaining why.' },
          ],
          hint: 'A corrected number without an explanation just raises the same question again next month.',
        },
        {
          worked_well: 'You gave Sana the reasoning behind the number, not just the number itself.',
          consider: 'Suggesting a way to catch this earlier next time turns a one-off fix into a lasting improvement.',
          skill: { title: 'Communicating uncertainty', text: 'Leadership decisions are better when they know not just the number, but how confident to be in it.' },
        },
      ),
    ],
  },

  software_developer: {
    focus: 'Debugging & Release Support',
    situation: 'Customers are reporting slow response times right after this morning’s release.',
    skills_used: ['Debugging', 'Communication', 'API design'],
    activities: [
      activity(
        'development_studio',
        'Slow Responses After a Release',
        {
          character_name: 'Sam',
          character_intro: 'He’s on support and is getting complaints about the order history page loading slowly since the release went out.',
          what_to_do: 'Decide what you would investigate first, and why.',
        },
        {
          question: 'Customers report the order history page has been slow since this morning’s release. What do you check first?',
          options: [
            { id: 'a', text: 'Compare this morning’s release changes against the monitoring data for that page.' },
            { id: 'b', text: 'Roll back this morning’s release straight away, then investigate.' },
            { id: 'c', text: 'Post an update for support and customers, then start gathering information.' },
          ],
          hint: 'What changed this morning is the fastest lead you have right now.',
        },
        {
          worked_well: 'You used the release as a starting point instead of investigating blind.',
          consider: 'A rollback is worth keeping in mind as a fallback if the cause isn’t obvious quickly.',
          skill: { title: 'Observability', text: 'Good monitoring around a release is what makes “compare against the release” possible in the first place.' },
        },
      ),
      activity(
        'testing_quality_lab',
        'Confirming the Fix',
        {
          character_name: 'Nadia',
          character_intro: 'She’s on QA and wants to make sure the fix for the slow page is actually verified before it goes out again.',
          what_to_do: 'Decide how you would confirm the fix works before it ships.',
        },
        {
          question: 'You’ve made a fix for the slow page. What do you do before it goes out again?',
          options: [
            { id: 'a', text: 'Add a test that reproduces the original slowdown, and confirm it now passes.' },
            { id: 'b', text: 'Ship it, since the fix addresses the change that caused the issue.' },
            { id: 'c', text: 'Ask Nadia to manually check the page loads quickly once.' },
          ],
          hint: 'A fix that isn’t tested against the original problem can regress without anyone noticing.',
        },
        {
          worked_well: 'You verified the fix against the actual problem, not just against your assumption of the cause.',
          consider: 'Checking the fix under realistic load (not just a single manual check) would build more confidence before release.',
          skill: { title: 'Regression testing', text: 'A test that reproduces a past incident is what stops the same bug from quietly coming back.' },
        },
      ),
      activity(
        'project_delivery_board',
        'Explaining the Delay',
        {
          character_name: 'Farah',
          character_intro: 'She manages the release schedule and needs to know if this incident affects tomorrow’s planned release.',
          what_to_do: 'Decide what you would tell her about tomorrow’s release.',
        },
        {
          question: 'Farah asks if today’s incident affects tomorrow’s planned release. What do you tell her?',
          options: [
            { id: 'a', text: 'Explain what caused today’s issue, whether it’s fixed, and what you’d still watch for tomorrow.' },
            { id: 'b', text: 'Tell her it’s fine, since today’s fix is already deployed.' },
            { id: 'c', text: 'Suggest delaying tomorrow’s release without explaining why.' },
          ],
          hint: 'She can only make a good call about tomorrow if she understands what actually happened today.',
        },
        {
          worked_well: 'You gave Farah the context behind the incident, not just a status update.',
          consider: 'Naming a specific thing to monitor after tomorrow’s release would help catch a repeat early.',
          skill: { title: 'Incident communication', text: 'Explaining the "why" behind an incident is what lets someone else make a good decision about what comes next.' },
        },
      ),
    ],
  },
  web_developer: {
    focus: 'Front-End Debugging',
    situation: 'Support is getting reports that the checkout page looks broken for some users since this morning’s release.',
    skills_used: ['Debugging', 'CSS', 'Cross-browser testing', 'Communication'],
    activities: [
      activity(
        'development_studio',
        'A Layout Bug on Launch Day',
        {
          character_name: 'Alex',
          character_intro: 'They handle support tickets and have a growing list of screenshots from confused customers.',
          what_to_do: 'Decide how you would reproduce the issue and what you would prioritise first.',
        },
        {
          question: 'Customers say checkout looks broken, but it works fine for you. What do you check first?',
          options: [
            { id: 'a', text: 'Ask which browser and device the reports are coming from.' },
            { id: 'b', text: 'Assume it’s a one-off and wait for more reports.' },
            { id: 'c', text: 'Rewrite the checkout layout from scratch to be safe.' },
          ],
          hint: 'A bug you can’t reproduce is usually a bug you haven’t matched the conditions for yet.',
        },
        {
          worked_well: 'You looked for what was different about the affected users before changing any code.',
          consider: 'Checking recent analytics for a spike in a specific browser or device would confirm it faster.',
          skill: { title: 'Cross-browser debugging', text: 'Most “can’t reproduce it” bugs come down to matching the exact browser, device or screen size that’s affected.' },
        },
      ),
    ],
  },
  web_and_digital_interface_designer: {
    focus: 'UX Design Collaboration',
    situation: 'Two stakeholders have given conflicting feedback on the new checkout flow, and the deadline is this week.',
    skills_used: ['User research', 'Prototyping', 'Stakeholder communication'],
    activities: [
      activity(
        'product_collaboration_studio',
        'Conflicting Feedback on a New Flow',
        {
          character_name: 'Jordan',
          character_intro: 'They lead product and want the flow simplified, while the support lead wants more confirmation steps to reduce errors.',
          what_to_do: 'Decide how you would reconcile the feedback and move forward.',
        },
        {
          question: 'Jordan wants fewer steps; support wants more confirmation. The deadline is this week. What do you do?',
          options: [
            { id: 'a', text: 'Ask both what problem they’re trying to solve, then look for a design that addresses both.' },
            { id: 'b', text: 'Go with whichever stakeholder asked first.' },
            { id: 'c', text: 'Split the difference without checking what either actually needs.' },
          ],
          hint: 'Conflicting requests often turn out to be two different problems, not one disagreement.',
        },
        {
          worked_well: 'You looked past the specific requests to the underlying problems each stakeholder was trying to solve.',
          consider: 'A quick prototype of the reconciled flow would let both stakeholders react to something concrete before the deadline.',
          skill: { title: 'Stakeholder reconciliation', text: 'Two people asking for opposite things are often solvable together once you know what each is actually worried about.' },
        },
      ),
    ],
  },
  computer_systems_analyst: {
    focus: 'Systems Requirements Analysis',
    situation: 'Two teams have submitted conflicting requirements for the same upcoming system change.',
    skills_used: ['Requirements gathering', 'Documentation', 'Stakeholder communication'],
    activities: [
      activity(
        'project_delivery_board',
        'A Conflicting System Requirement',
        {
          character_name: 'Dana',
          character_intro: 'She leads one of the two teams and is concerned the other team’s requirement will break her team’s workflow.',
          what_to_do: 'Decide how you would reconcile the two requirements.',
        },
        {
          question: 'Two teams have submitted requirements that can’t both be implemented as written. What do you do first?',
          options: [
            { id: 'a', text: 'Document both requirements and the specific point where they conflict, then bring both teams together.' },
            { id: 'b', text: 'Pick the requirement from the team that asked first.' },
            { id: 'c', text: 'Implement both separately and let the teams sort it out later.' },
          ],
          hint: 'A conflict is easier to resolve once both sides can see the exact same point of disagreement.',
        },
        {
          worked_well: 'You made the specific conflict visible instead of picking a side without discussion.',
          consider: 'Naming the trade-off each team would accept if the other requirement wins would speed up the conversation.',
          skill: { title: 'Requirements conflict resolution', text: 'Most requirement conflicts resolve faster once everyone agrees on exactly where they disagree.' },
        },
      ),
    ],
  },
  it_project_manager: {
    focus: 'Delivery & Risk Management',
    situation: 'A key deliverable looks like it will miss its deadline, and the client hasn’t been told yet.',
    skills_used: ['Planning', 'Stakeholder communication', 'Risk management'],
    activities: [
      activity(
        'stakeholder_client_studio',
        'A Slipping Deadline',
        {
          character_name: 'Leo',
          character_intro: 'He leads the delivery team and has just flagged that testing is running two weeks behind schedule.',
          what_to_do: 'Decide how you would respond, and who you would inform first.',
        },
        {
          question: 'Leo says testing is two weeks behind. The client hasn’t been told. What do you do first?',
          options: [
            { id: 'a', text: 'Confirm the real impact on the deadline with Leo, then tell the client early with a plan.' },
            { id: 'b', text: 'Wait to see if the team can catch up before saying anything.' },
            { id: 'c', text: 'Tell the client it will be late without a revised plan yet.' },
          ],
          hint: 'A client who hears about a delay early, with a plan, reacts very differently to one who hears late.',
        },
        {
          worked_well: 'You confirmed the actual impact before communicating anything, so the message to the client was accurate.',
          consider: 'Offering a couple of options (e.g. reduced scope vs. a new date) gives the client a choice, not just bad news.',
          skill: { title: 'Proactive risk communication', text: 'Surfacing a risk early, with a plan, keeps trust with a client in a way that surfacing it late rarely does.' },
        },
      ),
    ],
  },
  database_administrator: {
    focus: 'Database Performance & Reliability',
    situation: 'A report that used to run in seconds is now timing out in production.',
    skills_used: ['SQL', 'Performance tuning', 'Documentation'],
    activities: [
      activity(
        'data_analytics_lab',
        'A Slow Query in Production',
        {
          character_name: 'Priya',
          character_intro: 'She runs this report every morning for the leadership team and needs it working again before their 9am meeting.',
          what_to_do: 'Decide how you would diagnose and safely fix the slow query.',
        },
        {
          question: 'A report that used to run in seconds is now timing out. What do you check first?',
          options: [
            { id: 'a', text: 'Check the query’s execution plan to see what changed.' },
            { id: 'b', text: 'Restart the database server in case it’s a temporary issue.' },
            { id: 'c', text: 'Rewrite the report from scratch before investigating further.' },
          ],
          hint: 'The execution plan usually shows exactly where a once-fast query started doing more work.',
        },
        {
          worked_well: 'You looked at how the query is actually being run before making any changes.',
          consider: 'Checking whether the underlying data volume has grown significantly would confirm if this is a scaling issue, not just a one-off.',
          skill: { title: 'Query performance tuning', text: 'An execution plan shows where time is actually being spent, which is far more reliable than guessing.' },
        },
      ),
    ],
  },
  database_architect: {
    focus: 'Data Architecture & Schema Design',
    situation: 'A team has requested a schema change that could impact two other services sharing the same database.',
    skills_used: ['Data modelling', 'Documentation', 'Stakeholder communication'],
    activities: [
      activity(
        'development_studio',
        'A Schema Change Request',
        {
          character_name: 'Noah',
          character_intro: 'He leads the requesting team and needs an answer today so his team can plan their sprint.',
          what_to_do: 'Decide how you would evaluate the request and respond.',
        },
        {
          question: 'Noah’s schema change could affect two other services. He needs an answer today. What do you do?',
          options: [
            { id: 'a', text: 'Identify exactly which parts of the other services depend on the current schema, then respond with what’s safe.' },
            { id: 'b', text: 'Approve it today since Noah needs an answer.' },
            { id: 'c', text: 'Decline it without checking the actual impact.' },
          ],
          hint: 'A schema is shared infrastructure - the real question is what else is quietly relying on its current shape.',
        },
        {
          worked_well: 'You checked the actual dependencies before giving Noah an answer either way.',
          consider: 'Proposing a migration path (rather than a flat yes/no) could unblock Noah’s sprint while still protecting the other services.',
          skill: { title: 'Schema impact analysis', text: 'Before changing shared data structures, mapping who depends on the current shape avoids breaking things no one thought to check.' },
        },
      ),
    ],
  },
  data_scientist: {
    focus: 'Model Monitoring & Analysis',
    situation: 'A model’s predictions have shifted noticeably since last week, and the product team has noticed.',
    skills_used: ['Data analysis', 'Model evaluation', 'Communication'],
    activities: [
      activity(
        'data_analytics_lab',
        'A Model Behaving Unexpectedly',
        {
          character_name: 'Mei',
          character_intro: 'She manages the product relying on this model and wants to know if it can still be trusted.',
          what_to_do: 'Decide how you would investigate the shift before responding to her.',
        },
        {
          question: 'The model’s predictions shifted noticeably this week. What do you check first?',
          options: [
            { id: 'a', text: 'Check whether the input data distribution has changed since last week.' },
            { id: 'b', text: 'Retrain the model immediately with the same data and hope it corrects itself.' },
            { id: 'c', text: 'Tell Mei the model is fine, since nothing was changed on purpose.' },
          ],
          hint: 'A model’s behaviour usually shifts because what it’s seeing shifted, not because the model itself changed.',
        },
        {
          worked_well: 'You checked the input data before assuming the model itself was the problem.',
          consider: 'Comparing performance across different user segments could reveal if the shift only affects part of the population.',
          skill: { title: 'Data drift detection', text: 'A model’s inputs changing over time is one of the most common - and most overlooked - reasons predictions start to shift.' },
        },
      ),
    ],
  },
  information_security_analyst: {
    focus: 'Security Incident Response',
    situation: 'A monitoring alert has flagged an unusual login pattern on a customer-facing account overnight.',
    skills_used: ['Incident response', 'Log analysis', 'Documentation'],
    activities: [
      activity(
        'security_operations_room',
        'An Unusual Login Alert',
        {
          character_name: 'Chris',
          character_intro: 'They’re on the overnight shift and escalated this as soon as the pattern looked off.',
          what_to_do: 'Decide how you would investigate the alert and who you would notify.',
        },
        {
          question: 'An alert flags unusual login activity on a customer account overnight. What do you do first?',
          options: [
            { id: 'a', text: 'Check the login’s location and device against the account’s normal pattern.' },
            { id: 'b', text: 'Lock the account immediately without checking further.' },
            { id: 'c', text: 'Dismiss the alert since nothing else was reported overnight.' },
          ],
          hint: 'Confirming whether an alert is a real threat comes before deciding how to respond to it.',
        },
        {
          worked_well: 'You confirmed the pattern was genuinely unusual before deciding how to respond.',
          consider: 'Documenting the timeline as you go makes it much easier to hand this off or explain later.',
          skill: { title: 'Alert triage', text: 'Distinguishing a real anomaly from normal-but-unfamiliar behaviour is the first skill in not chasing false alarms.' },
        },
      ),
    ],
  },
  information_security_engineer: {
    focus: 'Vulnerability & Risk Management',
    situation: 'An automated scan has flagged a known vulnerability in a dependency used by a live service.',
    skills_used: ['Vulnerability management', 'Risk assessment', 'Communication'],
    activities: [
      activity(
        'security_operations_room',
        'A Vulnerable Dependency',
        {
          character_name: 'Robin',
          character_intro: 'They lead the affected service team and are asking how urgent this really is.',
          what_to_do: 'Decide how you would prioritise the fix and communicate the risk.',
        },
        {
          question: 'A scan flags a known vulnerability in a live service’s dependency. Robin asks how urgent it is. What do you tell them?',
          options: [
            { id: 'a', text: 'Check whether the vulnerable code path is actually reachable in this service before rating the urgency.' },
            { id: 'b', text: 'Tell them it’s critical, since the scanner flagged it.' },
            { id: 'c', text: 'Tell them it can wait, since nothing has gone wrong yet.' },
          ],
          hint: 'A flagged vulnerability and an exploitable one aren’t always the same thing.',
        },
        {
          worked_well: 'You checked whether the vulnerability was actually reachable before setting the urgency.',
          consider: 'Giving Robin a clear timeframe (not just a severity label) helps his team plan around it.',
          skill: { title: 'Risk-based prioritisation', text: 'A scanner’s severity score is a starting point - whether the vulnerable path is actually reachable is what determines real risk.' },
        },
      ),
    ],
  },
  computer_network_support_specialist: {
    focus: 'Network Troubleshooting',
    situation: 'A team keeps losing network connectivity for a few seconds at a time, several times a day.',
    skills_used: ['Network troubleshooting', 'Documentation', 'Communication'],
    activities: [
      activity(
        'network_infrastructure_hub',
        'An Intermittent Connectivity Issue',
        {
          character_name: 'Tia',
          character_intro: 'She sits with the affected team and says it’s been happening for two days, always around the same time.',
          what_to_do: 'Decide how you would narrow down the cause.',
        },
        {
          question: 'A team loses connectivity for a few seconds, several times a day, around the same time. What do you check first?',
          options: [
            { id: 'a', text: 'Check what else on the network is scheduled to run around that time.' },
            { id: 'b', text: 'Replace the team’s network hardware right away.' },
            { id: 'c', text: 'Tell Tia it’s probably unrelated to anything specific.' },
          ],
          hint: 'A pattern that repeats at the same time is usually caused by something else that also repeats at that time.',
        },
        {
          worked_well: 'You used the time pattern as a lead instead of jumping to a hardware fix.',
          consider: 'Checking whether other teams on the same network segment see the same drops would confirm how widespread it is.',
          skill: { title: 'Pattern-based troubleshooting', text: 'A recurring, time-based symptom is one of the strongest clues in network troubleshooting - it points to a specific cause, not a vague one.' },
        },
      ),
    ],
  },
  network_and_systems_administrator: {
    focus: 'Systems Administration',
    situation: 'A production server restarted overnight with no scheduled maintenance on record.',
    skills_used: ['System administration', 'Log analysis', 'Documentation'],
    activities: [
      activity(
        'network_infrastructure_hub',
        'An Unexpected Server Restart',
        {
          character_name: 'Omar',
          character_intro: 'He noticed a short outage in the monitoring dashboard this morning and wants to know what happened before it happens again.',
          what_to_do: 'Decide how you would investigate the unexpected restart.',
        },
        {
          question: 'A production server restarted overnight with no scheduled maintenance. What do you check first?',
          options: [
            { id: 'a', text: 'Check the system logs around the restart time for errors or resource limits.' },
            { id: 'b', text: 'Assume it was a one-off and monitor for now.' },
            { id: 'c', text: 'Restart the server again to see if it happens twice.' },
          ],
          hint: 'The logs from right before a restart almost always show what triggered it.',
        },
        {
          worked_well: 'You went straight to the logs from the restart window instead of waiting to see if it recurs.',
          consider: 'Checking resource usage trends over the past few days could reveal if this was building up rather than sudden.',
          skill: { title: 'Root-cause log analysis', text: 'The minutes right before an unexpected restart are where the actual trigger almost always shows up.' },
        },
      ),
    ],
  },
};

// A reasonable generic activity for a relevant area without hand-written
// content yet, so every relevant area still gets something concrete and
// real-feeling rather than a placeholder (AC 4.4.1).
function genericActivity(areaId, areaLabel, roleLabel) {
  return activity(
    areaId,
    'A New Priority Comes In',
    {
      character_name: 'A colleague',
      character_intro: `Someone in the ${areaLabel} has an unexpected, time-sensitive request that touches your work as a ${roleLabel.toLowerCase()}.`,
      what_to_do: 'Decide how you would prioritise this against your existing work.',
    },
    {
      question: `A colleague in the ${areaLabel} needs your help with something urgent that wasn’t on today’s plan. What do you do first?`,
      options: [
        { id: 'a', text: 'Ask what’s driving the urgency before deciding how to fit it in.' },
        { id: 'b', text: 'Drop what you’re doing and start on it immediately.' },
        { id: 'c', text: 'Tell them it will have to wait until your current work is done.' },
      ],
      hint: 'Not every urgent-sounding request is equally urgent once you understand why.',
    },
    {
      worked_well: 'You checked what was actually driving the request before committing to it.',
      consider: 'Letting the people affected by your current work know about the change keeps everyone’s expectations aligned.',
      skill: { title: 'Prioritisation', text: 'Understanding why something is urgent is what makes it possible to weigh it fairly against everything else on your plate.' },
    },
  )
}

// A full generic session for any role without specific hand-written
// content at all (falls back to a single general_workspace activity).
function genericSession(roleLabel) {
  return {
    focus: 'Workplace Practice',
    situation: 'A colleague needs your help with an unexpected, time-sensitive request.',
    skills_used: ['Communication', 'Prioritisation', 'Problem solving'],
    activities: [genericActivity('general_workspace', 'General Workspace', roleLabel)],
  }
}

// Returns the full practice session (focus, situation, and one activity
// per role-specific relevant area) for a role, filling in any relevant
// area that doesn't have hand-written content yet with a generic activity,
// so every relevant hotspot always opens something real.
export function getPracticeSession(roleId, roleLabel, relevantRoleAreaIds, areaLabelById) {
  const hand = SESSIONS[roleId]
  const areaIds = relevantRoleAreaIds && relevantRoleAreaIds.length > 0
    ? relevantRoleAreaIds
    : (hand ? hand.activities.map((a) => a.area_id) : ['general_workspace'])

  if (!hand) return genericSession(roleLabel || 'your role')

  const byArea = new Map(hand.activities.map((a) => [a.area_id, a]))
  const activities = areaIds.map((areaId) => byArea.get(areaId) || genericActivity(areaId, areaLabelById?.(areaId) || 'this area', roleLabel || 'your role'))

  return { focus: hand.focus, situation: hand.situation, skills_used: hand.skills_used, activities }
}
