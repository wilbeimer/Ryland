import { useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";

export default function CoursePage() {
   const { id } = useParams()
   const [course, setCourse] = useState(null)
   const [assignments, setAssignments] = useState([])
   const [title, setTitle] = useState('')
   const [type, setType] = useState('')
   const [loading, setLoading] = useState(true)

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

   return (
      <div className="page">
         <div className="course-page-banner" style={{ background: course?.color }} />
         <h1>{course?.name}</h1>
         <ul className="assignment-list">
            {assignments.map(assignment => (
               <li key={assignment.id} className="assignment-card" onClick={() => navigate(`/assignments/${assignment.id}`)}>
                  <span className="assignment-name">{assignment.title}</span>
               </li>
            ))} 
         </ul>

         <div className="assignment-form">
            <h2 className="form-title">Add an assignment</h2>
            <div className="form-row">
               <label htmlFor="atitle">Assignment Name</label>
               <input type="text" id="atitle" value={title} onChange={e => setTitle(e.target.value)} />
            </div>
            <div className="form-row">
               <label htmlFor="atype">Assignment Type</label>
               <select id="atype" value={type} onChange={e => setType(e.target.value)}>
                  <option value="">Select a type</option>
                  <option value="quiz">Quiz</option>
                  <option value="written">Written</option>
                  <option value="checklist">checklist</option>
               </select>
            </div>
            <button className="btn-primary" onClick={handleAddAssignment}>Add Assignment</button>
         </div>
      </div>
   )
}
