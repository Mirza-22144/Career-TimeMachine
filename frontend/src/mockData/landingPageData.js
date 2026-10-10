// Mock data for the Landing screen (frontend/src/screens/LandingPage.jsx).
// Nothing here is wired to the backend yet — replace with real API data later.

// Top navigation links, shared across every page via components/TopNav.jsx.
// `gated: true` marks a token-dependent destination - selecting it opens
// the Access Token Required page (AC 3.1.6) if there isn't one yet.
// `requireProfile: true` additionally requires a confirmed profile - these
// destinations all build on her career profile, so an incomplete one sends
// her back into the wizard at the first unfinished step instead (AC 3.3.3's
// rule, applied consistently to every page that depends on it). "Home" is
// the only link with neither requirement. Career Journey now lives in the
// profile dropdown (AC 3.1.7) rather than the top-level nav.
export const navLinks = [
  { label: "Home", href: "/", gated: false, requireProfile: false },
  { label: "Choose Your Path", href: "/choose-your-path", gated: true, requireProfile: true },
  { label: "Practice Scenarios", href: "/workplace-scenario", gated: true, requireProfile: true },
  { label: "Dashboard", href: "/dashboard", gated: true, requireProfile: true },
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

// "How it works" - one section that says what the site is and walks through
// it in the order she meets it. `stage` is the part of her journey a step
// belongs to; `result` is what she leaves that step with.
export const howItWorks = {
  heading: "Your journey, step by step.",
  intro:
    "CareerTimeMachine is a practice space for women returning to IT after a career break. It starts from the experience you already have, shows you where it can take you today, and lets you try the work before you go back.",
  steps: [
    {
      id: "token",
      stage: "START",
      title: "Get your access token",
      text: "One click, no account and no email. The token is your private key to come back later, on any device.",
      result: "A token to keep",
    },
    {
      id: "profile",
      stage: "REMEMBER",
      title: "Tell us your story",
      text: "Your previous IT role, the skills you used and when your break began. Three short screens.",
      result: "Your career profile",
    },
    {
      id: "path",
      stage: "DISCOVER",
      title: "Choose your path",
      text: "See the roles your experience points to, or paste a job description to compare it with your profile.",
      result: "A roadmap of skills",
    },
    {
      id: "practice",
      stage: "PRACTISE",
      title: "Try the work",
      text: "Short, realistic workplace activities for the role you chose. Nothing is graded.",
      result: "Feedback, never a score",
    },
    {
      id: "dashboard",
      stage: "MOVE FORWARD",
      title: "Follow your progress",
      text: "Your dashboard keeps your roadmap, the skills you have practised and your past feedback together.",
      result: "Confidence to return",
    },
  ],
  closing: "You can stop after any step and pick up where you left off.",
};

// Footer. The wordmark next to the logo is rendered in white (see
// LandingPage.jsx) since the footer uses the logo's dark-theme variant.
export const footerSection = {
  tagline:
    "Practice-based support for women returning to IT after a career break. Built around the experience you already have.",
  // `id` tells LandingPage.jsx what each link does.
  columns: [
    {
      heading: "PRODUCT",
      links: [
        { id: "how-it-works", label: "How it works" },
        { id: "dashboard", label: "Dashboard" },
        { id: "start", label: "Start your journey" },
      ],
    },
  ],
  copyright: "© 2026 CareerTimeMachine. All rights reserved.",
};
