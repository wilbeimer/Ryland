import { useEffect, useId, useRef, useState } from 'react'
import './CourseColorPicker.css'

/** Accent swatches only — course name stays on primary text for AA contrast. */
const COURSE_COLORS = [
  { value: '#e5446d', name: 'Rose' },
  { value: '#c62828', name: 'Red' },
  { value: '#0d7377', name: 'Teal' },
  { value: '#1f7a52', name: 'Green' },
  { value: '#8a5a00', name: 'Amber' },
  { value: '#2f6fed', name: 'Blue' },
  { value: '#455a64', name: 'Slate' },
] as const

type CourseColorPickerProps = {
  color: string
  disabled?: boolean
  onChange: (color: string) => void
}

function colorName(color: string): string {
  const match = COURSE_COLORS.find(({ value }) => value === color.toLowerCase())
  return match?.name ?? color
}

export function CourseColorPicker({
  color,
  disabled = false,
  onChange,
}: CourseColorPickerProps) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const swatchRef = useRef<HTMLButtonElement>(null)
  const restoreFocusRef = useRef(false)
  const paletteId = useId()
  const selected = color.toLowerCase()

  const closePalette = (restoreFocus: boolean) => {
    if (restoreFocus) {
      restoreFocusRef.current = true
    }
    setOpen(false)
  }

  useEffect(() => {
    if (!open && restoreFocusRef.current && !disabled) {
      restoreFocusRef.current = false
      swatchRef.current?.focus()
    }
  }, [open, disabled])

  useEffect(() => {
    if (!open) return

    const onPointerDown = (event: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        restoreFocusRef.current = true
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('mousedown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  return (
    <div ref={rootRef} className="course-color-picker">
      <button
        ref={swatchRef}
        type="button"
        className="course-color-picker__swatch"
        style={{ background: color }}
        aria-label={`Course color ${colorName(color)}`}
        aria-expanded={open}
        aria-controls={paletteId}
        disabled={disabled}
        onClick={() => setOpen((value) => !value)}
      />

      {open && (
        <div
          id={paletteId}
          className="course-color-picker__palette"
          role="group"
          aria-label="Course color options"
        >
          {COURSE_COLORS.map(({ value, name }) => {
            const isSelected = value === selected
            return (
              <button
                key={value}
                type="button"
                className={
                  isSelected
                    ? 'course-color-picker__option course-color-picker__option--selected'
                    : 'course-color-picker__option'
                }
                style={{ background: value }}
                aria-label={`Set course color to ${name}`}
                aria-pressed={isSelected}
                disabled={disabled}
                onClick={() => {
                  onChange(value)
                  closePalette(true)
                }}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}
