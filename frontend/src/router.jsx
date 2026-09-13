import { useEffect, useState } from 'react'
import LandingPage from './screens/LandingPage.jsx'
import YourStory from './screens/YourStory.jsx'
import YourExperience from './screens/YourExperience.jsx'
import YourBreak from './screens/YourBreak.jsx'
import SkillRelevanceMap from './screens/SkillRelevanceMap.jsx'
import YourDirection from './screens/YourDirection.jsx'
import CareerJourney from './screens/CareerJourney.jsx'
import WorkplaceScenario from './screens/WorkplaceScenario.jsx'
import { getCurrentPath } from './navigate.js'

// Path -> screen component. Add an entry here as each new screen is built.
const routes = {
  '/': LandingPage,
  '/your-story': YourStory,
  '/your-experience': YourExperience,
  '/your-break': YourBreak,
  '/skill-relevance-map': SkillRelevanceMap,
  '/your-direction': YourDirection,
  '/career-journey': CareerJourney,
  '/workplace-scenario': WorkplaceScenario,
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

  // Moving to a new step should always start at the top, not wherever the
  // previous step was scrolled to.
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [path])

  const Screen = routes[path] || LandingPage
  return <Screen />
}
