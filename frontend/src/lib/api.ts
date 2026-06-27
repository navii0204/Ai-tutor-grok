import axios from "axios";

const BASE = import.meta.env.VITE_API_BASE_URL || "";

export const api = axios.create({
  baseURL: `${BASE}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

// ── Student ────────────────────────────────────────────────────────────────────

export async function getStudentProfile(studentId: string) {
  const { data } = await api.get(`/student/profile/${studentId}`);
  return data;
}

export async function getDailyPlan(studentId: string) {
  const { data } = await api.get(`/student/daily-plan/${studentId}`);
  return data;
}

export async function sendChatMessage(payload: {
  student_id: string;
  concept_id: string;
  message: string;
  history: Array<{ role: string; content: string }>;
  session_id?: string;
}) {
  const { data } = await api.post("/student/chat", payload);
  return data as {
    response: string;
    is_question: boolean;
    focus_cue: string | null;
    reflection_prompt: string | null;
    mastery_delta: number;
  };
}

export async function simulatorCommand(payload: {
  student_id: string;
  simulator_id: string;
  command: string;
  params?: Record<string, unknown>;
  config?: Record<string, unknown>;
}) {
  const { data } = await api.post("/student/simulator/command", payload);
  return data;
}

// ── Teacher ───────────────────────────────────────────────────────────────────

export async function getClassroomInsights(tenantId: string, grade: string) {
  const { data } = await api.get(`/teacher/classroom/${tenantId}/grade/${grade}/insights`);
  return data;
}

export async function generateLessonPlan(payload: {
  concept_id: string;
  grade: string;
  segment: string;
  duration_minutes: number;
}) {
  const { data } = await api.post("/teacher/lesson-plan", payload);
  return data;
}
