import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"

export default function AssignmentPage() {
   const { id } = useParams()
   const [assignment, setAssignment]  = useState(null)
   const [submissions, setSubmissions] = useState([])
   const [loading, setLoading] = useState(true)

   useEffect(() => {
      fetch(`${import.meta.env.VITE_API_URL}/assignments/${id}`)
         .then(res => res.json())
         .then(data => {
            setAssignment(data)
            setLoading(false)
         })

      fetch(`${import.meta.env.VITE_API_URL}/assignments/${id}/submissions`)
         .then(res => res.json())
         .then(data => setSubmissions(data))
   }, [])


   if(loading) return <div className="page">Loading...</div>
   if (!assignment) return <div className="page">Course not found.</div>

   return (
      <div className="page">
         <h1>{ assignment?.title }</h1>

         <ul className="submission-list">
            {submissions.map(submission => (
               <li key={submission.id}>
                  <span>{submission.content}</span>
               </li>
            ))}
         </ul>
      </div>
   )
}
