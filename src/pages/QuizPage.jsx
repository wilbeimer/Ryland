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
      let correct = 0
      quiz.questions.forEach((q, i) => {
         if (q.type === 'multiple_choice' && q.options) {
            const selectedOption = q.options[answers[i]]
            if (selectedOption === q.answer) correct++
         }
      })
      setScore(correct)
      setSubmitted(true)
   }

   if (loading) return <div className="page">Loading...</div>
   if (!quiz) return <div className="page">Quiz not found.</div>

   const mcCount = quiz.questions.filter(q => q.type === 'multiple_choice').length

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
               const selectedOption = q.options?.[selected]
               const isCorrect = submitted && selectedOption === q.answer
               const isWrong = submitted && selected !== undefined && selectedOption !== q.answer

               return (
                  <div key={qi} className={`quiz-question ${submitted ? (isCorrect ? 'quiz-question--correct' : 'quiz-question--wrong') : ''}`}>
                     <p className="quiz-question-text">{qi + 1}. {q.question}</p>
                     {q.type === 'multiple_choice'
                        ? <ul className="quiz-choices">
                           {q.options.map((option, ci) => (
                              <li
                                 key={ci}
                                 className={`quiz-choice
${selected === ci ? 'quiz-choice--selected' : ''}
${submitted && option === q.answer ? 'quiz-choice--correct' : ''}
${submitted && selected === ci && option !== q.answer ? 'quiz-choice--wrong' : ''}
`}
                                 onClick={() => handleSelect(qi, ci)}
                              >
                                 {option}
                              </li>
                           ))}
                        </ul>
                        : <div className="short-answer">
                           {submitted
                              ? <p className="short-answer-answer">Answer: {q.answer}</p>
                              : <textarea
                                 rows={3}
                                 placeholder="Your answer..."
                                 value={answers[qi] || ''}
                                 onChange={e => setAnswers(prev => ({ ...prev, [qi]: e.target.value }))}
                              />
                           }
                        </div>
                     }
                  </div>
               )
            })}
         </div>

         {!submitted
            ? <button className="btn-primary" onClick={handleSubmit}>Submit Quiz</button>
            : <div className="quiz-result">
               <span className="quiz-score">{score} / {mcCount} correct</span>
            </div>
         }
      </div>
   )
}
