import { useEffect, useState } from 'react'
import '../styles/WorkplaceScenario.css'
import TopNav from '../components/TopNav'
import { api } from '../api.js'
import { navigate } from '../navigate.js'

// Reached after finishing the wizard (Your Direction's "Try a Workplace
// Scenario"), or from the nav's Practice Scenarios link once a token is
// active. The real feature (AI-generated scenarios, still Iteration 2
// backend/AI work) isn't built yet - this is a real, reachable page rather
// than a dead link, personalised with the chosen direction where possible.
export default function WorkplaceScenario() {
  const [areaLabel, setAreaLabel] = useState(null)

  useEffect(() => {
    async function load() {
      try {
        const [direction, careerAreas] = await Promise.all([
          api.getCareerDirection(),
          api.getCatalogue('career-areas'),
        ])
        setAreaLabel(careerAreas.find((a) => a.id === direction.area_to_explore)?.label)
      } catch {
        // No direction chosen yet (e.g. reached this page without finishing
        // the wizard) - the static copy below still makes sense on its own.
      }
    }
    load()
  }, [])

  return (
    <>
      <TopNav />
      <div className="ws-page">
        <main className="ws-content">
          <span className="ws-eyebrow">WORKPLACE SCENARIO</span>
          <h1 className="ws-heading">Workplace scenarios are coming soon.</h1>
          <p className="ws-subheading">
            This is where you&rsquo;ll be able to practise a realistic scenario
            {areaLabel ? ` for ${areaLabel}` : ' for your chosen direction'}.
          </p>

          <button type="button" className="ws-back-link" onClick={() => navigate('/career-journey')}>
            Back to Career Journey
          </button>
        </main>
      </div>
    </>
  )
}
