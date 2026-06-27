import { Routes, Route, Navigate } from "react-router-dom";
import StudentLayout from "./components/layouts/StudentLayout";
import ChatPage from "./components/chat/ChatPage";
import SimulatorPage from "./components/simulator/SimulatorPage";
import DashboardPage from "./components/dashboard/DashboardPage";
import TeacherLayout from "./components/layouts/TeacherLayout";
import TeacherDashboard from "./components/teacher/TeacherDashboard";

export default function App() {
  return (
    <Routes>
      {/* Student experience */}
      <Route path="/student" element={<StudentLayout />}>
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="chat/:conceptId?" element={<ChatPage />} />
        <Route path="simulator/:simId?" element={<SimulatorPage />} />
      </Route>

      {/* Teacher experience */}
      <Route path="/teacher" element={<TeacherLayout />}>
        <Route index element={<TeacherDashboard />} />
      </Route>

      {/* Default redirect */}
      <Route path="*" element={<Navigate to="/student/dashboard" replace />} />
    </Routes>
  );
}
