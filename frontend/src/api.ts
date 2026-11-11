export type Course = {
  id: string
  name: string
  description: string
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

export async function fetchCourses(): Promise<Course[]> {
  const response = await fetch(`${API_BASE}/courses`)
  if (!response.ok) {
    throw new Error(`Failed to load courses (${response.status})`)
  }
  return response.json()
}
