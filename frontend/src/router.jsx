import { useEffect, useState } from 'react'
import LandingPage from './screens/LandingPage.jsx'
import YourStory from './screens/YourStory.jsx'
import YourExperience from './screens/YourExperience.jsx'
import YourBreak from './screens/YourBreak.jsx'
import ProfileSetUp from './screens/ProfileSetUp.jsx'
import ChooseYourPath from './screens/ChooseYourPath.jsx'
import AccessTokenRequired from './screens/AccessTokenRequired.jsx'
import Dashboard from './screens/Dashboard.jsx'
import AnalyseJobDescription from './screens/AnalyseJobDescription.jsx'
import JobDescriptionComparison from './screens/JobDescriptionComparison.jsx'
import YourRoadmap from './screens/YourRoadmap.jsx'
import PracticeFeedbackView from './screens/PracticeFeedbackView.jsx'
import CareerJourney from './screens/CareerJourney.jsx'
import WorkplaceScenario from './screens/WorkplaceScenario.jsx'
import { getCurrentPath } from './navigate.js'

// Path -> screen component. Add an entry here as each new screen is built.
const routes = {
  '/': LandingPage,
  '/your-story': YourStory,
  '/your-experience': YourExperience,
  '/your-break': YourBreak,
  '/profile-set-up': ProfileSetUp,
  '/choose-your-path': ChooseYourPath,
  '/access-token-required': AccessTokenRequired,
  '/dashboard': Dashboard,
  '/analyse-job-description': AnalyseJobDescription,
  '/job-description-comparison': JobDescriptionComparison,
  '/your-roadmap': YourRoadmap,
  '/practice-feedback': PracticeFeedbackView,
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
