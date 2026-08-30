// Mock data for the "Your Story" onboarding wizard (shown after the
// Landing screen's "Enter My Journey" CTA). This is a real data-collection
// flow, not a demo preview — its inputs stay fully interactive.

// Steps shown in the wizard's sidebar. Only steps 1-4's content exists so
// far; step 5 renders as a pending placeholder until its design arrives.
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
  roleQuestion: 'What was your previous IT role?',
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

// Builds the reflection sentence shown under the years slider.
export function buildReflectionText(role, years) {
  const yearsLabel = years >= stepOneData.maxYears ? `${years}+` : `${years}`
  return `A ${role} with ${yearsLabel} years of experience. That is a significant professional foundation.`
}

// Step 2 — "Your Experience": technologies/tools used + main
// responsibilities. Nothing is pre-selected — the user builds this list
// themselves.
export const stepTwoData = {
  eyebrow: 'STEP 02 · YOUR EXPERIENCE',
  heading: 'What do you remember working with?',
  subheading: 'You do not need to remember everything. Start with what feels familiar.',
  skillsLabel: 'Technologies and tools',
  skills: [
    'Java',
    'Python',
    'JavaScript',
    'TypeScript',
    'SQL',
    'REST APIs',
    'Git',
    'AWS',
    'Azure',
    'Docker',
    'Testing',
    'Agile',
    'Data Analysis',
    'Kubernetes',
    'React',
    'Node.js',
  ],
  skillsQuote: 'There is no need to remember everything.',
  responsibilitiesLabel: 'Main responsibilities',
  responsibilities: [
    'Backend development',
    'API design',
    'Debugging & troubleshooting',
    'Testing & QA',
    'Code review',
    'System design',
    'Team collaboration',
    'Project delivery',
  ],
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
  reasons: ['Caregiving', 'Personal reasons', 'Health & wellbeing', 'Further study', 'Relocation', 'Other', 'Prefer not to say'],
  note: 'We use these dates to show what changed in your field while you were away.',
  ctaLabel: 'See My Skills Map',
}

export const sidePhoto = {
  label: 'YOU ARE IN GOOD COMPANY',
  value: '1 in 4',
  caption: 'women in tech have taken a career break',
}

// Step 4 — "Skill Relevance Map": what's still relevant + new horizons.
export const stepFourData = {
  eyebrow: 'STEP 04 · SKILL RELEVANCE MAP',
  heading: 'Your experience is still your greatest asset.',
  subheading: 'See what remains relevant and what you could explore.',
  newHorizons: [
    'Remote collaboration',
    'GitHub Copilot',
    'TypeScript',
    'Cloud-native',
    'AI-assisted tools',
    'React / Next.js',
    'Docker / K8s',
    'Modern security',
    'LLM APIs',
  ],
  skillNotes: {
    Java: 'Currently in demand for your role.',
    Python: 'Widely used across modern stacks.',
    SQL: 'Still core to most backend systems.',
    'REST APIs': 'A foundation for most integrations today.',
    Git: 'Still the standard for version control.',
    Testing: 'Increasingly automated, still essential.',
    Agile: 'Still the common way teams ship software.',
  },
  ctaLabel: 'Define My Direction',
}
