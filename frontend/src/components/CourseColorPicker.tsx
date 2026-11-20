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

export function CourseColorPicker({
  color,
  disabled = false,
  onChange,
}: CourseColorPickerProps) {
  const selected = color.toLowerCase()

  return (
    <div className="course-color-picker" role="group" aria-label="Course color">
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
            onClick={() => onChange(value)}
          />
        )
      })}
    </div>
  )
}
