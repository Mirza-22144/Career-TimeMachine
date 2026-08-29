import { useEffect, useState } from 'react'
import LandingPage from './screens/LandingPage.jsx'
import YourStory from './screens/YourStory.jsx'

// Path -> screen component. Add an entry here as each new screen is built.
const routes = {
  '/': LandingPage,
  '/your-story': YourStory,
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
