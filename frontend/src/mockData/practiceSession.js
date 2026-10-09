// MOCK DATA for the one workplace activity the AI team has not delivered
// yet: Code Review (screens/WorkplaceScenario.jsx).
//
// Multiple Choice and Drag and Drop are real - they come from
// POST /practice-sessions and are stored by the backend. Code Review is
// fixed content, the same for every role, and a completed one is only
// remembered in this browser (see practiceHistory.js). Replace
// loadMockActivities() with the real API call when its content arrives.

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
    file: { name: "checkout/total.py", language: "Python" },
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

];

// Code Review is offered to every role: the skills our database lists for
// each of the 27 roles include Python, Java or SQL, so no role can be
// ruled out as "not working with code" (team rule: if unsure, show it).
export async function loadMockActivities() {
  return ACTIVITIES;
}
