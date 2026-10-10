import { useEffect, useId, useRef, useState } from 'react'
import '../styles/YearCombobox.css'

// A year field she types into: the list underneath narrows as she types
// ("201" shows 2010 to 2019). She can also open the list and pick with the
// mouse or the arrow keys. Follows the WAI-ARIA combobox pattern.
//
// `value` is the chosen year as a string, or '' while nothing valid is
// chosen. `onChange` is only ever called with a year from `options`, or ''.
export default function YearCombobox({ id, value, onChange, options, disabled = false, startAtEnd = false }) {
  const listId = useId()
  const listRef = useRef(null)
  // What she has typed, while it differs from the chosen year.
  const [draft, setDraft] = useState(null)
  const [isOpen, setIsOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)

  const text = disabled ? '' : (draft ?? value)
  const matches = options.map(String).filter((year) => year.startsWith(text))
  const isUnknown = !disabled && draft !== null && draft !== '' && matches.length === 0
  const showList = isOpen && !disabled && matches.length > 0

  // Keep the highlighted year in view, and open a long unfiltered list at
  // the recent end when asked to (a break usually started in recent years).
  useEffect(() => {
    const list = listRef.current
    if (!list) return
    if (activeIndex >= 0) {
      list.children[activeIndex]?.scrollIntoView({ block: 'nearest' })
    } else {
      list.scrollTop = startAtEnd && text === '' ? list.scrollHeight : 0
    }
  }, [showList, activeIndex, startAtEnd, text])

  const choose = (year) => {
    setDraft(null)
    setIsOpen(false)
    setActiveIndex(-1)
    onChange(year)
  }

  const handleInput = (e) => {
    const typed = e.target.value.replace(/\D/g, '').slice(0, 4)
    setDraft(typed)
    setIsOpen(true)
    setActiveIndex(-1)
    onChange(options.map(String).includes(typed) ? typed : '')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault()
      if (matches.length === 0) return
      setIsOpen(true)
      const step = e.key === 'ArrowDown' ? 1 : -1
      setActiveIndex((index) => {
        if (index < 0) return step === 1 ? 0 : matches.length - 1
        return (index + step + matches.length) % matches.length
      })
    } else if (e.key === 'Enter' && showList && activeIndex >= 0) {
      e.preventDefault()
      choose(matches[activeIndex])
    } else if (e.key === 'Escape' && isOpen) {
      e.preventDefault()
      setIsOpen(false)
      setActiveIndex(-1)
    }
  }

  return (
    <div className="yc-root">
      <input
        id={id}
        type="text"
        inputMode="numeric"
        autoComplete="off"
        maxLength={4}
        className="yc-input"
        placeholder={disabled ? '' : 'Type a year'}
        role="combobox"
        aria-expanded={showList}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={showList && activeIndex >= 0 ? `${listId}-${matches[activeIndex]}` : undefined}
        aria-invalid={isUnknown || undefined}
        aria-describedby={isUnknown ? `${listId}-hint` : undefined}
        value={text}
        disabled={disabled}
        onChange={handleInput}
        onFocus={() => setIsOpen(true)}
        onClick={() => setIsOpen(true)}
        onBlur={() => {
          setIsOpen(false)
          setActiveIndex(-1)
        }}
        onKeyDown={handleKeyDown}
      />
      {showList && (
        <ul className="yc-list" id={listId} role="listbox" ref={listRef}>
          {matches.map((year, index) => (
            <li
              key={year}
              id={`${listId}-${year}`}
              role="option"
              aria-selected={year === value}
              className={`yc-option ${index === activeIndex ? 'yc-option--active' : ''} ${year === value ? 'yc-option--selected' : ''}`}
              // mousedown, not click: the input's blur would close the list first.
              onMouseDown={(e) => {
                e.preventDefault()
                choose(year)
              }}
            >
              {year}
            </li>
          ))}
        </ul>
      )}
      {isUnknown && (
        <p className="yc-hint" id={`${listId}-hint`} role="status">
          Choose a year between {options[0]} and {options.at(-1)}.
        </p>
      )}
    </div>
  )
}
