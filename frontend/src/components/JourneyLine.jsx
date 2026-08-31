import { useCallback, useEffect, useState } from 'react'
import '../styles/JourneyLine.css'
import { journeyMilestones } from '../mockData/landingPageData'

/**
 * Scroll progress rail shown down the page, tracking the milestones listed
 * in mockData/landingPageData.js (journeyMilestones).
 *
 * Each marker's position is worked out fresh from where its section sits on
 * the page right now, instead of a fixed number, so it stays right even if
 * a section's content changes size. Which marker is "active" is tracked on
 * its own, based on which section is currently on screen.
 *
 * `containerRef` must point at the parent element (.lp-page) this rail is
 * placed inside.
 */

// Each section has 120px of space above its heading. Markers are moved down
// by this much past the section's top edge, so they land inside that
// section instead of right on the line between two sections.
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
        // Move down past the section's top edge so the marker sits inside
        // this section instead of on the line between two sections.
        const top = el.getBoundingClientRect().top + window.scrollY - containerTop + SECTION_ENTRY_OFFSET
        return { ...m, top }
      })
      .filter(Boolean)
    setPositions(next)
  }, [containerRef])

  // Must stay a plain effect, not useLayoutEffect. `containerRef` belongs
  // to JourneyLine's parent element, and that ref is not set yet at the
  // point a child's useLayoutEffect would run. A plain effect runs later,
  // once every ref on the page is ready.
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
