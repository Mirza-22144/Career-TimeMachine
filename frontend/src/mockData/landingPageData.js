// Mock data for the Landing screen (frontend/src/screens/LandingPage.jsx).
// Nothing here is wired to the backend yet — replace with real API data later.

// Top navigation links. `clickable: false` renders the link as inert text
// (see LandingPage.jsx) for destinations not yet built.
export const navLinks = [
  { label: "How it works", href: "#remember", clickable: true },
  { label: "Practise", href: "#practise", clickable: false },
  { label: "Your ePortfolio", href: "#", clickable: false },
];

export const trustItems = [
  "Private and secure",
  "No account required",
  "Your journey is yours",
];

// Waypoints overlaid on the hero photograph. Position values are the exact
// left/top px from the Figma frame (1440x1024 hero panel context).
export const heroWaypoints = [
  { step: "01", label: "Remember", left: 146, top: 581, active: true },
  { step: "02", label: "Discover", left: 321, top: 461, active: false },
  { step: "03", label: "Practise", left: 479, top: 351, active: false },
  { step: "04", label: "Move Forward", left: 590, top: 287, active: false },
];

// "Remember" section — Experience Constellation: a center profile node with
// floating skill pills connected by dashed lines.
export const experienceProfile = {
  role: "Software Engineer",
  tenure: "8 years before the break",
};

export const experienceSkills = [
  { id: "sql", name: "SQL", left: 512, top: 80 },
  {
    id: "java",
    name: "Java",
    left: 800,
    top: 158,
    contextLabel: "Experience you can carry forward",
  },
  { id: "testing", name: "Testing", left: 878, top: 292 },
  { id: "rest-apis", name: "REST APIs", left: 700, top: 398 },
  { id: "agile", name: "Agile", left: 300, top: 442 },
];

// "Discover" section — Career Translation Map. The only interactive section
// on this screen: hovering/focusing a past skill highlights the future
// horizons it maps to. `leadsTo` lists which horizon ids light up.
export const pastSkills = [
  { id: "java", name: "Java", leadsTo: ["cloud-devops", "ai-ml"] },
  { id: "testing", name: "Testing", leadsTo: ["cloud-devops"] },
  {
    id: "rest-apis",
    name: "REST APIs",
    leadsTo: ["cloud-devops", "data-engineering"],
  },
  {
    id: "problem-solving",
    name: "Problem Solving",
    leadsTo: ["ai-ml", "cyber-security"],
  },
];

export const newHorizons = [
  {
    id: "cloud-devops",
    name: "Cloud & DevOps",
    description: "Where your systems thinking fits",
  },
  {
    id: "data-engineering",
    name: "Data Engineering",
    description: "Where your systems thinking fits",
  },
  {
    id: "ai-ml",
    name: "AI & ML",
    description: "Where your systems thinking fits",
  },
  {
    id: "cyber-security",
    name: "Cyber Security",
    description: "Where your systems thinking fits",
  },
];

// Default skill shown "active" before the user hovers anything, matching the
// static Figma frame (Java pre-highlighted).
export const defaultActiveSkillId = "java";

// "Adapt" section — the Practice Loop diagram. Positions are exact px,
// relative to the 1112x560 "Practice Loop" container in Figma.
export const adaptSection = {
  heading: "Your next practice changes with you.",
  subheading: "What you do shapes what comes next.",
  loopNodes: [
    { id: "your-response", label: "Your response", left: 490, top: 41.5 },
    { id: "feedback", label: "Feedback", left: 703, top: 186.5 },
    { id: "reflection", label: "Reflection", left: 624, top: 421 },
    { id: "next-practice", label: "Next practice", left: 369, top: 421 },
    { id: "your-progress", label: "Your progress", left: 292, top: 186.5 },
  ],
  adaptivePromptText: "Ready for something more challenging?",
  // Small flow-direction arrow markers between each loop node, evenly spaced
  // around the ring. Position = center point (computed from the Figma vector
  // bounding boxes); rotation = tangent angle for clockwise flow (derived
  // from each point's angle around the ring center, +90°) since Figma only
  // gave bounding boxes, not rotation, for these.
  loopArrows: [
    { x: 679, y: 99, rotation: 36 },
    { x: 757, y: 336, rotation: 108 },
    { x: 555, y: 480, rotation: 180 },
    { x: 358, y: 334, rotation: 252 },
    { x: 432, y: 101, rotation: 324 },
  ],
};

// "Reflect" section — confidence curve + mood selector.
// Dot centers/radii/opacity computed from the exact Figma ellipse boxes,
// relative to the 1112x280 "Confidence Path" container.
export const reflectSection = {
  heading: "See how far you’ve come.",
  subheading: "Progress you can actually see.",
  confidenceCurve: {
    points: [
      { x: 190, y: 236, r: 5, opacity: 0.45 },
      { x: 330, y: 206, r: 6.25, opacity: 0.59 },
      { x: 470, y: 166, r: 7.5, opacity: 0.73 },
      { x: 610, y: 120, r: 8.75, opacity: 0.87 },
      { x: 750, y: 72, r: 10, opacity: 1, glow: true },
    ],
    startLabel: { text: "START", left: 60, top: 258 },
    readyLabel: { text: "READY", left: 828, top: 48 },
  },
  question: "How do you feel about your progress?",
  moods: [
    { id: "still-finding", label: "Still finding my feet" },
    { id: "getting-there", label: "Getting there" },
    { id: "more-confident", label: "More confident" },
    { id: "ready", label: "Ready when you are" },
  ],
  defaultMoodId: "more-confident",
  nextIntentText: "I know what I want to practise next.",
};

// "ePortfolio" section — stacked-card preview mockup + caption.
export const eportfolioSection = {
  heading: "Turn your journey into something you can keep.",
  preview: {
    title: "Your return-to-work ePortfolio",
    subtitle: "Software Engineer  ·  Built as you went",
    badge: "Yours to keep",
    sections: [
      {
        id: "professional-background",
        title: "Professional Background",
        description: "Role, years and the ground you covered",
        active: true,
      },
      {
        id: "skills-technologies",
        title: "Skills & Technologies",
        description: "What you kept and what you added",
        active: false,
      },
      {
        id: "practice-journey",
        title: "Practice Journey",
        description: "Scenarios you worked through",
        active: false,
      },
      {
        id: "reflections-growth",
        title: "Reflections & Growth",
        description: "What you noticed about yourself",
        active: false,
      },
    ],
  },
  captionEyebrow: "THE RESULT OF YOUR JOURNEY",
  captionText: "A personal record of your return-to-work practice and growth.",
};

// "Closing" section — dark full-bleed CTA banner (reuses the hero photo).
// The CTA button itself uses the shared `journeyCtaLabel` in LandingPage.jsx
// rather than its own label.
export const closingSection = {
  lineBefore: "From wondering where to start...",
  lineAfter: "...to knowing what’s next.",
  subtext: "Your experience. Your practice. Your next step.",
};

// Footer. The wordmark next to the logo is rendered in white (see
// LandingPage.jsx) since the footer uses the logo's dark-theme variant.
export const footerSection = {
  tagline:
    "Practice-based support for women returning to IT after a career break. Built around the experience you already have.",
  columns: [
    {
      heading: "PRODUCT",
      links: [
        "How it works",
        "Practise scenarios",
        "Your ePortfolio",
        "Start your journey",
      ],
    },
    { heading: "SUPPORT", links: ["Contact us"] },
    {
      heading: "LEGAL",
      links: ["Privacy policy", "Terms of use", "Data and consent"],
    },
  ],
  copyright: "© 2026 CareerTimeMachine. All rights reserved.",
};

// "Practise" section — the Practice Window's scenario content.
// Fixed demo scenario: "check-logs" carries the real feedback copy and
// stays permanently selected; the other 3 options render for visual
// completeness but aren't clickable.
export const practiceScenario = {
  url: "careertimemachine.me / practice",
  scenarioLabel: "SCENARIO 01 · INCIDENT RESPONSE",
  question:
    "A service is down in production. Users are affected. What would you do first?",
  defaultSelectedId: "check-logs",
  options: [
    {
      id: "check-logs",
      label: "Check logs",
      feedback: {
        heading: "Supportive feedback",
        main: "Good starting point. Checking the logs helps identify the root cause.",
        note: "There is no single right answer. What matters is how you reason about it.",
      },
    },
    { id: "restart-service", label: "Restart service" },
    { id: "rollback-deployment", label: "Rollback deployment" },
    { id: "monitor-alerts", label: "Monitor alerts" },
  ],
  // Stage indicator shown under the feedback card. Only "Practise" has
  // content right now — Learn/Improve aren't specced, so they're inert.
  stages: ["PRACTISE", "LEARN", "IMPROVE"],
  activeStage: "PRACTISE",
};

// Page-long scroll progress rail (rendered by components/JourneyLine.jsx).
// Each milestone highlights as its linked section (`sectionId`) scrolls into
// view. `top` is unused by the renderer (which computes live positions from
// the DOM) and kept only as the original reference offset. `pending` flags
// any milestone whose caption still needs confirming against the design.
export const journeyMilestones = [
  {
    id: "remember",
    step: "01",
    title: "REMEMBER",
    caption: "My experience",
    top: -16,
    sectionId: "remember",
    pending: false,
  },
  {
    id: "discover",
    step: "02",
    title: "DISCOVER",
    caption: "What is relevant today",
    top: 910,
    sectionId: "discover",
    pending: false,
  },
  {
    id: "practise",
    step: "03",
    title: "PRACTISE",
    caption: "Try it before you return",
    top: 1743,
    sectionId: "practise",
    pending: false,
  },
  {
    id: "adapt",
    step: "04",
    title: "GROW",
    caption: "Feedback and reflection",
    top: 2641,
    sectionId: "adapt",
    pending: false,
  },
  {
    id: "move-forward",
    step: "05",
    title: "MOVE FORWARD",
    caption: "Confidence to return",
    top: 4421,
    sectionId: "eportfolio",
    pending: false,
  },
];
