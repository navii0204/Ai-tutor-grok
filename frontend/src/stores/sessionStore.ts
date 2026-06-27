import { create } from "zustand";
import type { StudentSummary } from "../lib/api";

interface Message {
  role: "student" | "tutor";
  content: string;
  focus_cue?: string | null;
  reflection_prompt?: string | null;
}

interface SessionState {
  studentId: string;
  sessionId: string | null;
  conceptId: string;
  messages: Message[];
  isLoading: boolean;
  students: StudentSummary[];
  setStudentId: (id: string) => void;
  setConceptId: (id: string) => void;
  setSessionId: (id: string) => void;
  addMessage: (msg: Message) => void;
  appendToLastMessage: (char: string) => void;
  setLoading: (v: boolean) => void;
  clearMessages: () => void;
  setStudents: (students: StudentSummary[]) => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  studentId: "6d8ea3f0-8049-48be-a854-26af4f4fa12c",  // Arjun Sharma (seeded)
  sessionId: null,
  conceptId: "sci_photosynthesis",
  messages: [],
  isLoading: false,
  students: [],
  setStudentId: (id) => set({ studentId: id }),
  setConceptId: (id) => set({ conceptId: id, messages: [] }),
  setSessionId: (id) => set({ sessionId: id }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  appendToLastMessage: (char) =>
    set((s) => {
      if (s.messages.length === 0) return s;
      const msgs = [...s.messages];
      msgs[msgs.length - 1] = {
        ...msgs[msgs.length - 1],
        content: msgs[msgs.length - 1].content + char,
      };
      return { messages: msgs };
    }),
  setLoading: (v) => set({ isLoading: v }),
  clearMessages: () => set({ messages: [] }),
  setStudents: (students) => set({ students }),
}));
