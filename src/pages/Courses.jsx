import { useNavigate } from "react-router-dom"
import { useState, useEffect } from "react"

export default function Courses() {
   const [courses, setCourses] = useState([])
   const [name, setName] = useState('')
   const [color, setColor] = useState('#6c63ff')
   const [description, setDescription] = useState('')
   const navigate = useNavigate()

   useEffect(() => {
      fetch(`${import.meta.env.VITE_API_URL}/courses`)
         .then(res => res.json())
         .then(data => setCourses(data))
   }, [])

   useEffect(() => {
      const pending = courses.filter(c => c.status === 'pending')
      if (pending.length === 0) return

      let delay = 3000
      let timeout

      function poll(){
         pending.forEach( course => {
            fetch(`${import.meta.env.VITE_API_URL}/courses/${course.id}`)
               .then(res => res.json())
               .then(updated => {
                  if (updated.status !== 'pending') {
                     setCourses(prev => prev.map(c => c.id === updated.id ? updated : c))
                  }
              })
         })
         delay = Math.min(delay * 1.5, 15000)
         timeout = setTimeout(poll, delay)
      }

      timeout = setTimeout(poll, delay)
      return () => clearInterval(timeout)
   }, [courses])

   function addCourse() {
      console.log("posting to:", `${import.meta.env.VITE_API_URL}/courses`)

      fetch(`${import.meta.env.VITE_API_URL}/courses`, {
         method: "POST",
         headers: { "Content-Type": "application/json" },
         body: JSON.stringify({ name, description, color })
      })
      .then(res => res.json())
      .then(data => setCourses([...courses, data]))
   }

   function deleteCourse(id) {
      fetch(`${import.meta.env.VITE_API_URL}/courses/${id}`, {
         method: "DELETE"
      })
      .then(() => setCourses(courses.filter(c => c.id !== id)))
   }

   function handleAddCourse() {
      if (!name.trim()) return
      addCourse({ name, color, description })
      setName('')
      setColor('#6c63ff')
      setDescription('')
   }

   return (
      <div className="page">
         <h1 className="page-title">Courses</h1>

         <div className="course-form">
            <h2 className="form-title">Add a Course</h2>
            <div className="form-row">
               <label htmlFor="cname">Course Name</label>
               <input type="text" id="cname" value={name} onChange={e => setName(e.target.value)} />
            </div>
            <div className="form-row">
               <label htmlFor="cdescription">Description</label>
               <input type="text" id="cdescription" value={description} onChange={e => setDescription(e.target.value)} />
            </div>
            <div className="form-row">
               <label htmlFor="ccolor">Color</label>
               <input type="color" id="ccolor" value={color} onChange={e => setColor(e.target.value)} />
            </div>
            <button className="btn-primary" onClick={handleAddCourse}>Add Course</button>
         </div>

         <ul className="course-list">
            {courses.map(course => (
               <li key={course.id} className={`course-card ${course.status === 'pending' ? 'course-card--pending' : ''}`}
                  onClick={() => course.status === 'completed' && navigate(`/courses/${course.id}`)}>
                  <div className="course-card-banner" style={{ background: course.color }} />
                  <div className="course-card-body">
                     <div className="course-card-info">
                        <span className="course-name">{course.name}</span>
                        {course.status === 'pending'
                           ? <span className="course-status">Generating curriculum...</span>
                           : <span className="course-description">{course.description}</span>
                        }
                        {course.status === 'failed' && <span className="course-status course-status--failed">Generation failed</span>}
                     </div>
                     <button className="btn-danger" onClick={(e) => {
                        e.stopPropagation()
                        deleteCourse(course.id)
                     }}>Delete</button>
                  </div>
               </li>
            ))} 
         </ul>
      </div>
   )
}
