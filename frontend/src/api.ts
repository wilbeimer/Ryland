export type Course = {
  id: string
  name: string
  description: string
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
