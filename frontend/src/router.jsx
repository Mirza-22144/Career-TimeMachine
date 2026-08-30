import { useEffect, useState } from 'react'
import LandingPage from './screens/LandingPage.jsx'
import YourStory from './screens/YourStory.jsx'
import YourExperience from './screens/YourExperience.jsx'
import YourBreak from './screens/YourBreak.jsx'
import SkillRelevanceMap from './screens/SkillRelevanceMap.jsx'

// Path -> screen component. Add an entry here as each new screen is built.
const routes = {
  '/': LandingPage,
  '/your-story': YourStory,
  '/your-experience': YourExperience,
  '/your-break': YourBreak,
  '/skill-relevance-map': SkillRelevanceMap,
}

function getCurrentPath() {
  const hash = window.location.hash.replace(/^#/, '')
  return hash || '/'
}

// Renders whichever screen matches the current URL hash, and re-renders on
// navigation (see navigate.js). Falls back to the Landing screen for any
// unrecognized path.
export default function Router() {
  const [path, setPath] = useState(getCurrentPath)

  useEffect(() => {
    const onHashChange = () => setPath(getCurrentPath())
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const Screen = routes[path] || LandingPage
  return <Screen />
}
