import { Routes, Route } from "react-router-dom"
import Layout from "./Layout"
import Dashboard from "./pages/Dashboard"
import Courses from "./pages/Courses"
import Assignments from "./pages/Assignments"
import Grades from "./pages/Grades"
import CoursePage from "./pages/CoursePage"
import AssignmentPage from "./pages/AssignmentPage"

export default function App() {
   return (
      <Routes>
         <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="courses" element={<Courses />} />
            <Route path="courses/:id" element={<CoursePage />} />
            <Route path="assignments" element={<Assignments />} />
            <Route path="assignments/:id" element={<AssignmentPage />} />
            <Route path="grades" element={<Grades />} />
         </Route>
      </Routes>
   )
}
