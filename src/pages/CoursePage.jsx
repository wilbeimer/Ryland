import { useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";

export default function CoursePage() {
   const { id } = useParams()
   const [course, setCourse] = useState(null)
   const [assignments, setAssignments] = useState([])
   const [title, setTitle] = useState('')
   const [type, setType] = useState('')
   const [loading, setLoading] = useState(true)
   const weeks = [...new Set(assignments.map(a => a.week))].sort((a, b) => a - b)

   useEffect(() => {
      fetch(`${import.meta.env.VITE_API_URL}/courses/${id}`)
         .then(res => res.json())
         .then(data => {
            setCourse(data)
            setLoading(false)
         })

      fetch(`${import.meta.env.VITE_API_URL}/courses/${id}/assignments`)
         .then(res => res.json())
         .then(data => setAssignments(data))
   }, [])

   const navigate = useNavigate()

   if(loading) return <div className="page">Loading...</div>
   if (!course) return <div className="page">Course not found.</div>

   function handleAddAssignment() {
      if (!title.trim() || !type) return
      fetch(`${import.meta.env.VITE_API_URL}/assignments`, {
         method: "POST",
         headers: { "Content-Type": "application/json" },
         body: JSON.stringify({ courseId: id, title, type })
      })
         .then(res => res.json())
         .then(data => setAssignments([...assignments, data]))
      setTitle('')
      setType('')
   }

   console.log("textbook:", course.textbook)

   return (
      <div className="page">
         <div className="course-page-banner" style={{ background: course?.color }} />
         <h1>{course?.name}</h1>
         {course.description && (
            <p className="course-description">{course.description}</p>
         )}

         {course.textbook?.title && (
            <div className="course-textbook">
               <h2>Course Textbook</h2>

               {course.textbook?.url ? (
                  <a href={course.textbook.url} target="_blank" rel="noreferrer">{course.textbook.title}</a>
               ) : (
                     <span>{course.textbook.title}</span>
               )}
               <span className="author">{course.textbook.author}</span>
               <p>{course.textbook.description}</p>
            </div>
         )}

         {weeks.map(week => (
            <div key={week} className="week-group">
               <h2 className="week-title">Week {week}</h2>
               <ul className="assignment-list">
                  {assignments
                     .filter(a => a.week === week)
                     .map(assignment => (
                        <li key={assignment.id} className="assignment-card" onClick={() => navigate(`/assignments/${assignment.id}`)}>
                           <div className="assignment-card-info">
                              <span className="assignment-name">{assignment.title}</span>
                           </div>
                           <span className="assignment-type">{assignment.type}</span>
                        </li>
                     ))
                  }
               </ul>
            </div>
         ))}
      </div>
   )
}
