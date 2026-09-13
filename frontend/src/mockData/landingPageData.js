// Mock data for the Landing screen (frontend/src/screens/LandingPage.jsx).
// Nothing here is wired to the backend yet — replace with real API data later.

// Top navigation links. `clickable: false` renders the link as inert text
// (see LandingPage.jsx) for destinations not yet built. "Career Journey"
// scrolls to the in-page Roadmap slide, not the real /career-journey route -
// that route needs onboarding data a first-time anonymous visitor does not
// have yet.
export const navLinks = [
  { label: "Home", href: "#hero", clickable: true },
  { label: "Career Journey", href: "#roadmap", clickable: true },
  { label: "Practice Scenarios", href: "#", clickable: false },
  { label: "ePortfolio", href: "#", clickable: false },
];

export const trustItems = [
  "Private and secure",
  "No account required",
  "Your journey is yours",
];

// "Numbers" slide - real, sourced figures only (no invented statistics).
// The two team-figures also appear in mockData/onboardingData.js; kept in
// sync manually since each screen's mock data file is self-contained.
export const statsSection = {
  intro:
    "Technology moves fast, and a career break can make it feel impossible to catch up. You're not the only one - and you're not starting from zero.",
  stats: [
    { id: "career-break", value: "1 in 4", label: "Women in tech have taken a career break" },
    { id: "leave-by-35", value: "45%", label: "Of women in tech leave the industry by age 35" },
    { id: "avg-experience", value: "8.4 yrs", label: "Average IT experience on this platform" },
  ],
};

// "Roadmap" slide - the product's 5-step story, shown as a static diagram.
export const roadmapSteps = [
  { id: "remember", step: "01", title: "REMEMBER", caption: "My experience" },
  { id: "discover", step: "02", title: "DISCOVER", caption: "What is relevant today" },
  { id: "practice", step: "03", title: "PRACTICE", caption: "Try it before you return" },
  { id: "adapt", step: "04", title: "GROW", caption: "Feedback and reflection" },
  { id: "move-forward", step: "05", title: "MOVE FORWARD", caption: "Confidence to return" },
];

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
        "Practice scenarios",
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
