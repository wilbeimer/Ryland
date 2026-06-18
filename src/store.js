import {create} from 'zustand'
import { persist } from 'zustand/middleware'

function uuid() {
   return crypto.randomUUID()
}

export const useStore = create(
   persist(
      (set, get) => ({
         courses: [],
         assignments: [],
         submissions: [],

         // Courses
         addCourse: ({name, color, description}) =>
            set(state => ({
               courses: [...state.courses, { id: uuid(), name, color, description }]
            })),

         deleteCourse: (id) =>
            set(state => ({
               courses: state.courses.filter(c => c.id !== id),
               assignments: state.assignments.filter(a => a.courseId !== id)
            })),

         // Assignments
         addAssignment: ({courseId, title, type, dueDate = '', points = 100, content = {} }) =>
            set(state => ({
               assignments: [...state.assignments, {
                  id: uuid(),
                  courseId, title, type, dueDate, points, content,
                  createdAt: new Date().toISOString()
               }]
            })),

         deleteAssignment: (id) =>
            set(state => ({
               assignments: state.assignments.filter(a => a.id !== id),
               submissions: state.submissions.filter(s => s.assignmentID !== id)
            })),

         // Submissions
         addSubmission: ({assignmentID, grade, feedback, answers}) =>
            set(state => ({
               submissions: [...state.submissions, {
                  id: uuid(),
                  assignmentID, grade, feedback, answers,
                  submittedAt: new Date().toISOString()
               }]
            })),

         getSubmission: (assignmentID) => 
            get().submissions.find(s => s.assignmentID === assignmentID) || null,
      }),
      { name: 'curriculum-score' }
   )
)
         
