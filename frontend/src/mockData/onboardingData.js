// Mock data for the "Your Story" onboarding wizard (shown after the
// Landing screen's "Enter My Journey" CTA). This is a real data-collection
// flow, not a demo preview — its inputs stay fully interactive.

// Steps shown in the wizard's sidebar. Only step 1's content exists so far;
// steps 2-5 render as pending placeholders until their designs arrive.
export const onboardingSteps = [
  { id: 1, title: 'Your Story', subtitle: 'Where you started' },
  { id: 2, title: 'Your Experience', subtitle: 'What you built' },
  { id: 3, title: 'Your Break', subtitle: 'What changed' },
  { id: 4, title: 'Skill Relevance Map', subtitle: 'What is relevant now' },
  { id: 5, title: 'Your Direction', subtitle: 'Where you want to go' },
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
export const stepOneData = {
  eyebrow: 'STEP 01 · YOUR STORY',
  heading: 'Let us remember where your journey began.',
  subheading: 'Choose the role that started your professional story.',
  roleQuestion: 'What was your previous IT role? (select all that apply)',
  searchPlaceholder: 'Search your previous role...',
  roles: [
    'Software Engineer',
    'Software Developer',
    'Systems Analyst',
    'QA Engineer',
    'Web Developer',
    'IT Support Specialist',
    'Business Analyst',
    'Data Analyst',
    'Project Manager',
  ],
  experienceQuestion: 'How many years of IT experience did you have?',
  minYears: 1,
  maxYears: 10,
  ctaLabel: 'Continue',
}

// Joins role names into a natural-language list: "X", "X and Y", or
// "X, Y and Z".
function joinRoles(roles) {
  if (roles.length === 1) return roles[0]
  if (roles.length === 2) return `${roles[0]} and ${roles[1]}`
  return `${roles.slice(0, -1).join(', ')} and ${roles[roles.length - 1]}`
}

// Builds the reflection sentence shown under the years slider. `roles` is
// one or more previously-held IT roles.
export function buildReflectionText(roles, years) {
  const yearsLabel = years >= stepOneData.maxYears ? `${years}+` : `${years}`
  return `A ${joinRoles(roles)} with ${yearsLabel} years of experience. That is a significant professional foundation.`
}
