// MOCK DATA for the two workplace activities the AI team has not delivered
// yet: Code Review and Drag and Drop (screens/WorkplaceScenario.jsx).
//
// Multiple-choice practice is real - it comes from POST /practice-sessions
// and is stored by the backend. These two are fixed content, the same for
// every role, and a completed one is only remembered in this browser (see
// practiceHistory.js). Replace loadMockActivities() with the real API call
// when their content arrives.

const ACTIVITIES = [
  {
    id: "arjun-review",
    type: "code_review",
    areaId: "development_studio",
    announcement: "Something has come in at the Development Studio.",
    panel: {
      title: "Arjun wants a second pair of eyes",
      text: "He has changed how checkout totals are worked out and would like it looked over before it goes any further.",
      cta: "Take a look",
    },
    title: "Arjun’s change to checkout totals",
    file: { name: "checkout/total.py", language: "Python", note: "Written with an AI assistant" },
    firstLine: 12,
    code: [
      "def order_total(items, discount):",
      "    total = 0",
      "    for item in items:",
      "        total += item.price * item.qty",
      "    return total - discount",
    ],
    from: "Arjun",
    quote: "I used an AI assistant to tidy up how the order total is worked out. Could you look it over before I merge?",
    prompt: "What kind of issue does this have?",
    promptCaption: "Read the code, then choose the one that fits best.",
    hint: "Think about what each value could be when this runs on a real order.",
    options: [
      {
        id: "syntax",
        text: "A syntax error, so it would not run",
        workedWell: "You checked whether the code would run at all, which is the right first question.",
        consider: "This code does run. Consider what happens when a value is missing rather than how it is written.",
      },
      {
        id: "no-discount",
        text: "It can fail when an order has no discount",
        workedWell: "You noticed that the function assumes every order comes with a discount.",
        consider: "Consider also what should happen when the discount is larger than the total.",
      },
      {
        id: "naming",
        text: "Naming or formatting only",
        workedWell: "You looked at readability, which matters when code is written with an AI assistant.",
        consider: "The names are clear here. Consider what each value could be when this runs on a real order.",
      },
      {
        id: "none",
        text: "No issue to raise",
        workedWell: "You read the code through and found it easy to follow.",
        consider: "Code that looks finished can still assume too much. Consider an order that has no discount at all.",
      },
    ],
    skillToExplore: {
      skill: "Defensive coding",
      why: "Checking for missing or unexpected values before using them, which matters when code looks finished.",
    },
    skillsUsed: ["Code review", "Python"],
  },
  {
    id: "priya-update",
    type: "drag_and_drop",
    areaId: "project_delivery_board",
    announcement: "The Project & Delivery Board needs attention.",
    panel: {
      title: "Priya needs an update",
      text: "The checkout fix will miss today’s release and she has not been told. You led this piece of work, so the message should come from you before stand-up.",
      cta: "Write the update",
    },
    title: "Tell Priya where the fix stands",
    instruction: "Complete the message. Three of the five phrases fit.",
    to: "Priya · Checkout fix, update before stand-up",
    // Text and gaps in order; a gap is { gap: index }.
    message: ["Hi Priya, the checkout total fix", { gap: 0 }, ", so I have", { gap: 1 }, "and I will", { gap: 2 }, "."],
    hint: "A clear update says where things stand, what you have done, and what happens next.",
    phrases: [
      {
        id: "hopefully",
        text: "should hopefully be fine",
        fits: false,
        comesAcross: "“Hopefully” reads as uncertain, so Priya cannot plan around it.",
        better: "Say plainly whether the fix will make today’s release.",
      },
      {
        id: "paused",
        text: "paused the rollout so no more orders are affected",
        fits: true,
        comesAcross: "Shows you have already acted, which is what she needs to hear next.",
      },
      {
        id: "some-point",
        text: "let you know at some point",
        fits: false,
        comesAcross: "“At some point” leaves her without a time to plan around.",
        better: "Give a time she can expect to hear from you.",
      },
      {
        id: "not-ready",
        text: "will not be ready for today’s release",
        fits: true,
        comesAcross: "Clear and direct. Priya knows straight away that the release is affected.",
      },
      {
        id: "confirm",
        text: "confirm a new date by 3pm tomorrow",
        fits: true,
        comesAcross: "Gives her a time she can plan around.",
      },
    ],
    skillsUsed: ["Escalation updates", "Stakeholder communication"],
  },
];

// AC 4.4.4 / 4.7.1: Code Review is only for roles that work with code.
// Decided here by role until the backend serves this activity; a role
// typed in by hand ("other") is treated as not working with code.
const ROLES_WORKING_WITH_CODE = new Set([
  "blockchain_engineer",
  "business_intelligence_analyst",
  "computer_and_information_research_scientist",
  "computer_programmer",
  "computer_systems_engineer_architect",
  "data_scientist",
  "data_warehousing_specialist",
  "database_administrator",
  "database_architect",
  "information_security_engineer",
  "penetration_tester",
  "software_developer",
  "software_qa_analyst_tester",
  "video_game_designer",
  "web_administrator",
  "web_developer",
]);

// The mock activities this role can be given.
export async function loadMockActivities(roleId) {
  return ACTIVITIES.filter((item) => item.type !== "code_review" || ROLES_WORKING_WITH_CODE.has(roleId));
}

// Every mock activity, for re-reading feedback whatever her role is now.
export async function loadAllMockActivities() {
  return ACTIVITIES;
}
