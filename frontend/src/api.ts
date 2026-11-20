export type Course = {
  id: string
  name: string
  description: string
}

export type Week = {
  id: string
  week_number: number
  description: string
}

export type AssignmentType = 'text' | 'quiz'

export type Assignment = {
  id: string
  type: AssignmentType
  name: string
  description: string
  rubric: Record<string, unknown>
  due_date: string
}

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(
  /\/$/,
  '',
)

function isCourse(value: unknown): value is Course {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  const course = value as Record<string, unknown>
  return (
    typeof course.id === 'string' &&
    typeof course.name === 'string' &&
    typeof course.description === 'string'
  )
}

function isWeek(value: unknown): value is Week {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  const week = value as Record<string, unknown>
  return (
    typeof week.id === 'string' &&
    typeof week.week_number === 'number' &&
    typeof week.description === 'string'
  )
}

function isAssignment(value: unknown): value is Assignment {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  const assignment = value as Record<string, unknown>
  return (
    typeof assignment.id === 'string' &&
    (assignment.type === 'text' || assignment.type === 'quiz') &&
    typeof assignment.name === 'string' &&
    typeof assignment.description === 'string' &&
    typeof assignment.rubric === 'object' &&
    assignment.rubric !== null &&
    typeof assignment.due_date === 'string'
  )
}

export async function fetchCourses(): Promise<Course[]> {
  const response = await fetch(`${API_BASE}/courses`)
  if (!response.ok) {
    throw new Error(`Failed to load courses (${response.status})`)
  }

  const data: unknown = await response.json()
  if (!Array.isArray(data) || !data.every(isCourse)) {
    throw new Error('Failed to load courses (unexpected response)')
  }

  return data
}

export async function fetchWeeks(courseId: string): Promise<Week[]> {
  const response = await fetch(`${API_BASE}/courses/${courseId}/weeks`)
  if (!response.ok) {
    throw new Error(`Failed to load weeks (${response.status})`)
  }

  const data: unknown = await response.json()
  if (!Array.isArray(data) || !data.every(isWeek)) {
    throw new Error('Failed to load weeks (unexpected response)')
  }

  return data
}

/** Skips items with unknown `type` so a future assignment kind doesn't blank a week. */
export async function fetchAssignments(weekId: string): Promise<Assignment[]> {
  const response = await fetch(`${API_BASE}/weeks/${weekId}/assignments`)
  if (!response.ok) {
    throw new Error(`Failed to load assignments (${response.status})`)
  }

  const data: unknown = await response.json()
  if (!Array.isArray(data)) {
    throw new Error('Failed to load assignments (unexpected response)')
  }

  return data.filter(isAssignment)
}
