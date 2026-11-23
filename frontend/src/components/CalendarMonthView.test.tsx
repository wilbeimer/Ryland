import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { CalendarMonthView } from './CalendarMonthView'

describe('CalendarMonthView', () => {
  it('places coursework on the due day with course color accent', () => {
    render(
      <CalendarMonthView
        weeks={[
          {
            start_date: '2026-03-02',
            end_date: '2026-03-08',
            assignments: [
              {
                id: 'a1',
                type: 'text',
                name: 'Alg essay',
                description: 'Write',
                rubric: {},
                due_date: '2026-03-04T23:59:00-05:00',
                course_id: 'c1',
                course_name: 'Algebra',
                course_color: '#e5446d',
              },
            ],
          },
        ]}
      />,
    )

    expect(screen.getByRole('heading', { name: 'March 2026' })).toBeInTheDocument()
    expect(screen.getByText('Alg essay')).toBeInTheDocument()
    expect(screen.getByText('Algebra')).toBeInTheDocument()
    const item = screen.getByText('Alg essay').closest('.calendar-month__item')
    expect(item).toHaveStyle({
      ['--assignment-course-color' as string]: '#e5446d',
    })
  })
})
