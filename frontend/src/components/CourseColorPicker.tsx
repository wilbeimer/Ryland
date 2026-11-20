import './CourseColorPicker.css'

/** Accent swatches only — course name stays on primary text for AA contrast. */
const COURSE_COLORS = [
  '#e5446d',
  '#c62828',
  '#0d7377',
  '#1f7a52',
  '#8a5a00',
  '#2f6fed',
  '#455a64',
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
      {COURSE_COLORS.map((option) => {
        const isSelected = option === selected
        return (
          <button
            key={option}
            type="button"
            className={
              isSelected
                ? 'course-color-picker__option course-color-picker__option--selected'
                : 'course-color-picker__option'
            }
            style={{ background: option }}
            aria-label={`Set course color to ${option}`}
            aria-pressed={isSelected}
            disabled={disabled}
            onClick={() => onChange(option)}
          />
        )
      })}
    </div>
  )
}
