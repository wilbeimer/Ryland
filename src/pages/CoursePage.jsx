import { useParams } from "react-router-dom";
import { useStore } from "../store";
import { useState } from "react";

export default function CoursePage() {
   const { id } = useParams()
   const { courses, assignments, addAssignment } = useStore()
   const course = courses.find(c => c.id === id)
   const [title, setTitle] = useState('')
   const [type, setType] = useState('')

   if (!course) {return (<div className="page">Course not found.</div>)}

   function handleAddCourse() {
      if (!title.trim() || !type) return
      addAssignment({ courseId: id, title, type })
      setTitle('')
      setType('')
   }

   return (
      <div className="page">
         <div className="course-page-banner" style={{ background: course.color }} />
         <h1>{course.name}</h1>
         <ul className="assignment-list">
            {assignments.filter(a => a.courseId === id).map(assignment => (
               <span className="assignment-name">{assignment.title}</span>
            ))} 
         </ul>

         <div className="assignment-form">
            <h2 className="form-title">Add a assignment</h2>
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
            <button className="btn-primary" onClick={handleAddCourse}>Add Assignment</button>
         </div>
      </div>
   )
}
