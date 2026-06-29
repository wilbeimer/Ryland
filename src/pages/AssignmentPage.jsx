import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"

export default function AssignmentPage() {
   const { id } = useParams()
   const [assignment, setAssignment] = useState(null)
   const [submissions, setSubmissions] = useState([])
   const [loading, setLoading] = useState(true)
   const [submissionContent, setSubmissionContent] = useState("")

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

   // Poll pending submissions
   useEffect(() => {
      const pending = submissions.filter(s => s.status === 'pending')
      if (pending.length === 0) return

      const interval = setInterval(() => {
         pending.forEach(sub => {
            fetch(`${import.meta.env.VITE_API_URL}/submissions/${sub.id}`)
               .then(res => res.json())
               .then(updated => {
                  if (updated.status !== 'pending') {
                     setSubmissions(prev => prev.map(s => s.id === updated.id ? updated : s))
                  }
               })
         })
      }, 3000)

      return () => clearInterval(interval)
   }, [submissions])

   function handleAddSubmission() {
      if (!submissionContent.trim()) return
      fetch(`${import.meta.env.VITE_API_URL}/submissions`, {
         method: "POST",
         headers: { "Content-Type": "application/json" },
         body: JSON.stringify({ assignmentId: id, content: submissionContent })
      })
         .then(res => res.json())
         .then(data => setSubmissions(prev => [...prev, data]))
      setSubmissionContent('')
   }

   if (loading) return <div className="page">Loading...</div>
   if (!assignment) return <div className="page">Assignment not found.</div>

   return (
      <div className="page">
         <div className="assignment-header">
            <div className="assignment-meta">
               <span className="assignment-week">Week {assignment.week}</span>
               <span className="assignment-type">{assignment.type}</span>
            </div>
            <h1 className="page-title">{assignment.title}</h1>
            {assignment.description && (
               <p className="assignment-description">{assignment.description}</p>
            )}
         </div>

         {assignment.requirements?.length > 0 && (
            <div className="assignment-requirements">
               <h2>Requirements</h2>
               <ul>
                  {assignment.requirements.map((req, i) => (
                     <li key={i}>{req}</li>
                  ))}
               </ul>
            </div>
         )}

         {assignment.resources?.length > 0 && (
            <div className="assignment-resources">
               <h2>Supplimental Resources</h2>
               <ul>
                  {assignment.resources.map((r, i) => (
                     <li key={i}>
                        <a href={r.url} target="_blank" rel="noreferrer">{r.title}</a>
                        <span className="resource-type">{r.type}</span>
                        <p>{r.description}</p>
                     </li>
                  ))}
               </ul>
            </div>
         )}

         <div className="assignment-submissions">
            <h2>Submissions</h2>
            {submissions.length === 0
               ? <p className="empty-state">No submissions yet.</p>
               : <ul className="submission-list">
                  {submissions.map(submission => (
                     <li key={submission.id} className={`submission-card ${submission.status === 'pending' ? 'submission-card--pending' : ''}`}>
                        <p className="submission-content">{submission.content}</p>
                        {submission.status === 'pending' && (
                           <p className="submission-grading">Grading in progress...</p>
                        )}
                        {submission.status === 'failed' && (
                           <p className="submission-failed">Grading failed.</p>
                        )}
                        {submission.status === 'completed' && (
                           <div className="submission-grade">
                              <span className="submission-score">Grade: {submission.grade} / 100</span>
                              {submission.feedback && <p className="submission-feedback">{submission.feedback}</p>}
                           </div>
                        )}
                     </li>
                  ))}
               </ul>
            }

            {assignment.type !== 'quiz'
               ? <div className="submission-form">
                  <h3 className="form-title">Add a Submission</h3>
                  <div className="form-row">
                     <label htmlFor="scontent">Content</label>
                     <textarea
                        id="scontent"
                        value={submissionContent}
                        onChange={e => setSubmissionContent(e.target.value)}
                        rows={6}
                        placeholder="Write your submission here..."
                     />
                  </div>
                  <button className="btn-primary" onClick={handleAddSubmission}>Submit</button>
               </div>

               : <p className="empty-state"> Quiz submissions coming soon. </p>
            }
         </div>
      </div>
   )
}
