// Mock data for the "Your Story" onboarding wizard (shown after the
// Landing screen's "Enter My Journey" CTA). This is a real data-collection
// flow, not a demo preview — its inputs stay fully interactive.

// Steps shown in the wizard's sidebar. Only steps 1-4's content exists so
// far; step 5 renders as a pending placeholder until its design arrives.
export const onboardingSteps = [
  { id: 1, title: 'Your Story', subtitle: 'Where you started', path: '/your-story' },
  { id: 2, title: 'Your Experience', subtitle: 'What you built', path: '/your-experience' },
  { id: 3, title: 'Your Break', subtitle: 'What changed', path: '/your-break' },
  { id: 4, title: 'Skill Relevance Map', subtitle: 'What is relevant now', path: '/skill-relevance-map' },
  { id: 5, title: 'Your Direction', subtitle: 'Where you want to go', path: '/your-direction' },
]

export const sidebarBrand = {
  tagline: 'Your experience. Your comeback. Your future.',
}

export const sidebarStat = {
  label: 'WOMEN IN THIS PLATFORM HAVE',
  value: '8.4 yrs',
  caption: 'average IT experience',
}

export const sidebarQuote = 'Every expert started somewhere.'

// Step 1 — "Your Story": previous IT role + years of experience.
// Role and experience OPTIONS now come from the backend catalogue
// (GET /catalogue/roles, /catalogue/experience-options) — only the static
// screen copy lives here.
export const stepOneData = {
  eyebrow: 'STEP 01 · YOUR STORY',
  heading: 'Let us remember where your journey began.',
  subheading: 'Choose the role that started your professional story.',
  roleQuestion: 'What was your previous IT role?',
  searchPlaceholder: 'Search your previous role...',
  experienceQuestion: 'How many years of IT experience did you have?',
  ctaLabel: 'Continue',
}

// Builds the reflection sentence. `role` and `years` are catalogue labels
// (e.g. "Software Engineer", "5 years"), not raw ids.
export function buildReflectionText(role, years) {
  return `A ${role} with ${years} of experience. That is a significant professional foundation.`
}

// Step 2 — "Your Experience": technologies/tools used + main
// responsibilities. Nothing is pre-selected — the user builds this list
// themselves.
export const stepTwoData = {
  eyebrow: 'STEP 02 · YOUR EXPERIENCE',
  heading: 'What do you remember working with?',
  subheading: 'You do not need to remember everything. Start with what feels familiar.',
  skillsLabel: 'Technologies and tools',
  skillsQuote: 'There is no need to remember everything.',
  responsibilitiesLabel: 'Main responsibilities',
  translateNote: 'We will translate this into the language employers use today.',
  ctaLabel: 'Continue',
}

// Step 3 — "Your Break": when the break started/ends + optional reasons.
export const stepThreeData = {
  eyebrow: 'STEP 03 · YOUR BREAK',
  heading: 'Then life took you somewhere different.',
  subheading: 'When did your career break begin, and when are you planning to return?',
  startLabel: 'CAREER BREAK STARTED',
  returnLabel: 'PLANNING TO RETURN',
  reasonsLabel: 'What led to your break?',
  otherReasonPlaceholder: 'Tell us in your own words...',
  note: 'We use these dates to show what changed in your field while you were away.',
  invalidRangeMessage: 'Your planning-to-return year must be the same as or after your career break start year.',
  ctaLabel: 'See My Skills Map',
}

export const sidePhoto = {
  label: 'YOU ARE IN GOOD COMPANY',
  value: '1 in 4',
  caption: 'women in tech have taken a career break',
}

// Step 4 — "Skill Relevance Map". Skill-to-career-area connections come
// from the real backend (GET /career-translation) — only static screen
// copy lives here.
export const stepFourData = {
  eyebrow: 'STEP 04 · SKILL RELEVANCE MAP',
  heading: 'Your experience is still your greatest asset.',
  subheading: 'See what remains relevant and what you could explore.',
  ownedSummary: 'These are the skills you are bringing back.',
  ownedLabel: '● SKILLS YOU BRING BACK',
  areasLabel: '○ CONNECTED CAREER AREAS',
  noAreasMessage: 'No career-area connections found for your recorded skills yet.',
  skillNoAreaNote: 'Not currently mapped to a specific career area.',
  ctaLabel: 'Define My Direction',
}

// Step 5 — "Your Direction": pace + areas to explore + one to try first.
// Return-readiness options and career areas come from the backend
// catalogue (GET /catalogue/return-statuses, /career-areas); captions below
// are local flavour text keyed by the backend's option id, since the
// catalogue only provides a label.
export const paceCaptions = {
  ready: 'I am actively exploring roles now.',
  preparing: 'I am rebuilding confidence and updating my skills.',
  planning_soon: 'I am getting ready for my next opportunity.',
  not_sure: 'I am exploring what is possible for me.',
}

export const stepFiveData = {
  eyebrow: 'STEP 05 · YOUR DIRECTION',
  heading: 'Your direction from here.',
  subheading: 'Here is the journey you have mapped. Now choose where you are and what you want to explore next.',
  journeyLabel: 'YOUR JOURNEY SO FAR',
  paceQuestion: 'Where are you now?',
  paceSubtext: 'Choose the pace that feels right for you. There is no wrong answer.',
  areaQuestion: 'Which area would you like to explore?',
  areaSubtext: 'We will put you into a real workplace scenario for the area you choose.',
  noteTitle: 'You choose the pace.',
  noteBody: 'You are building on experience you already have, not starting from nothing.',
  ctaLabel: 'Try a Workplace Scenario',
}
