import { useCallback, useEffect, useState } from 'react'
import '../styles/JourneyLine.css'
import { journeyMilestones } from '../mockData/landingPageData'

/**
 * Page-long scroll progress rail tracking the milestones in
 * mockData/landingPageData.js (journeyMilestones).
 *
 * Each marker's vertical position is computed live from where its linked
 * section actually sits in the DOM (via `getBoundingClientRect`), rather
 * than a fixed offset, so the rail stays correct as section content changes.
 * The currently-active marker is tracked separately via IntersectionObserver
 * as sections scroll through the viewport.
 *
 * `containerRef` must point at the positioned ancestor (.lp-page) this rail
 * is absolutely positioned against.
 */

// Every section shares the same 120px top padding before its heading. Each
// marker is nudged this far past its section's top edge so it reads as
// sitting inside that section (rather than pinned to the seam where the
// previous section ends) while still landing comfortably before the
// heading text starts.
const SECTION_ENTRY_OFFSET = 40

export default function JourneyLine({ containerRef }) {
  const [positions, setPositions] = useState([])
  const [activeId, setActiveId] = useState(journeyMilestones[0].id)

  const recalc = useCallback(() => {
    const container = containerRef.current
    if (!container) return
    const containerTop = container.getBoundingClientRect().top + window.scrollY
    const next = journeyMilestones
      .map((m) => {
        const el = document.getElementById(m.sectionId)
        if (!el) return null
        // Nudge past the section's raw top edge (the seam where the
        // previous section ends) so the marker reads as sitting inside
        // this section, not floating on the boundary between two.
        const top = el.getBoundingClientRect().top + window.scrollY - containerTop + SECTION_ENTRY_OFFSET
        return { ...m, top }
      })
      .filter(Boolean)
    setPositions(next)
  }, [containerRef])

  // NOTE: this must be a plain effect, not useLayoutEffect. `containerRef`
  // (pageRef) is attached to JourneyLine's *parent* (.lp-page), and React
  // attaches a parent's ref only after processing its children — so at the
  // point a child's own useLayoutEffect fires, an ancestor ref can still be
  // null. Plain effects run after the whole commit (all refs) settles.
  useEffect(() => {
    recalc()
    window.addEventListener('resize', recalc)
    return () => window.removeEventListener('resize', recalc)
  }, [recalc])

  useEffect(() => {
    const sections = journeyMilestones
      .map((m) => ({ id: m.id, el: document.getElementById(m.sectionId) }))
      .filter((s) => s.el)
    if (!sections.length) return

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const match = sections.find((s) => s.el === entry.target)
            if (match) setActiveId(match.id)
          }
        })
      },
      { rootMargin: '-45% 0px -45% 0px', threshold: 0 }
    )
    sections.forEach((s) => observer.observe(s.el))
    return () => observer.disconnect()
  }, [])

  if (positions.length < 2) return null

  const lineTop = positions[0].top
  const lineBottom = positions[positions.length - 1].top
  const activeIndex = journeyMilestones.findIndex((m) => m.id === activeId)

  return (
    <div className="jl-rail" style={{ top: lineTop }} aria-hidden="true">
      <div className="jl-line" style={{ height: lineBottom - lineTop }} />
      {positions.map((milestone, index) => (
        <div
          key={milestone.id}
          className={`jl-milestone ${index <= activeIndex ? 'jl-milestone--passed' : ''} ${
            milestone.id === activeId ? 'jl-milestone--active' : ''
          }`}
          style={{ top: milestone.top - lineTop }}
        >
          <span className="jl-dot" />
          <span className="jl-label">
            <span className="jl-step">
              {milestone.step} {milestone.title}
            </span>
            <span className="jl-caption">
              {milestone.caption}
              {milestone.pending && <span className="jl-pending-tag"> (TBC)</span>}
            </span>
          </span>
        </div>
      ))}
    </div>
  )
}
