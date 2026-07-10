import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"

export default function QuizPage() {
   const { id } = useParams()
   const [quiz, setQuiz] = useState(null)
   const [loading, setLoading] = useState(true)
   const [answers, setAnswers] = useState({})
   const [submitted, setSubmitted] = useState(false)
   const [score, setScore] = useState(null)

   useEffect(() => {
      fetch(`${import.meta.env.VITE_API_URL}/quizzes/${id}`)
         .then(res => res.json())
         .then(data => {
            setQuiz(data)
            setLoading(false)
         })
   }, [])

   function handleSelect(questionIndex, choiceIndex) {
      if (submitted) return
      setAnswers(prev => ({ ...prev, [questionIndex]: choiceIndex }))
   }

   function handleSubmit() {
      if (Object.keys(answers).length < quiz.questions.length) return
      let correct = 0
      quiz.questions.forEach((q, i) => {
         if (answers[i] === q.correct_index) correct++
      })
      setScore(correct)
      setSubmitted(true)
   }

   if (loading) return <div className="page">Loading...</div>
   if (!quiz) return <div className="page">Quiz not found.</div>

   return (
      <div className="page">
         <div className="assignment-header">
            <div className="assignment-meta">
               <span className="assignment-week">Week {quiz.week}</span>
               <span className="assignment-type">Quiz</span>
            </div>
            <h1 className="page-title">{quiz.title}</h1>
         </div>

         <div className="quiz-questions">
            {quiz.questions.map((q, qi) => {
               const selected = answers[qi]
               const isCorrect = submitted && selected === q.correct_index
               const isWrong = submitted && selected !== q.correct_index

               return (
                  <div key={qi} className={`quiz-question ${submitted ? (isCorrect ? 'quiz-question--correct' : 'quiz-question--wrong') : ''}`}>
                     <p className="quiz-question-text">{qi + 1}. {q.question}</p>
                     <ul className="quiz-choices">
                        {q.choices.map((choice, ci) => (
                           <li
                              key={ci}
                              className={`quiz-choice
                                 ${selected === ci ? 'quiz-choice--selected' : ''}
                                 ${submitted && ci === q.correct_index ? 'quiz-choice--correct' : ''}
                                 ${submitted && selected === ci && ci !== q.correct_index ? 'quiz-choice--wrong' : ''}
                              `}
                              onClick={() => handleSelect(qi, ci)}
                           >
                              {choice}
                           </li>
                        ))}
                     </ul>
                  </div>
               )
            })}
         </div>

         {!submitted
            ? <button className="btn-primary" onClick={handleSubmit}>Submit Quiz</button>
            : <div className="quiz-result">
               <span className="quiz-score">{score} / {quiz.questions.length} correct</span>
            </div>
         }
      </div>
   )
}
