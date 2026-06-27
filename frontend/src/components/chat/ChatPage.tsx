import { useRef, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Sparkles } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { listConcepts, sendChatMessageStream } from "../../lib/api";
import { useSessionStore } from "../../stores/sessionStore";

export default function ChatPage() {
  const params = useParams();
  const {
    studentId, conceptId, messages, isLoading, sessionId, students,
    addMessage, appendToLastMessage, setLoading, setConceptId, clearMessages,
  } = useSessionStore();
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  // Derive segment from selected student (needed for concept list)
  const selectedStudent = students.find((s) => s.id === studentId);
  const segment = selectedStudent?.segment ?? "school";

  const { data: concepts = [] } = useQuery({
    queryKey: ["concepts", segment],
    queryFn: () => listConcepts(segment),
    staleTime: 10 * 60 * 1000,
  });

  useEffect(() => {
    if (params.conceptId) setConceptId(params.conceptId);
  }, [params.conceptId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const currentConceptName =
    concepts.find((c) => c.id === conceptId)?.name ?? conceptId;

  async function handleSend() {
    if (!input.trim() || isLoading) return;
    const userMsg = input.trim();
    setInput("");
    addMessage({ role: "student", content: userMsg });
    addMessage({ role: "tutor", content: "" });  // placeholder bubble for streaming
    setLoading(true);

    try {
      const history = messages.map((m) => ({
        role: m.role === "student" ? "user" : "assistant",
        content: m.content,
      }));
      await sendChatMessageStream(
        { student_id: studentId, concept_id: conceptId, message: userMsg,
          history, session_id: sessionId ?? undefined },
        (char) => appendToLastMessage(char),
        () => setLoading(false),
      );
    } catch {
      appendToLastMessage("I'm having a little trouble connecting. Try again in a moment?");
      setLoading(false);
    }
  }

  const lastMsg = messages[messages.length - 1];
  const isWaitingForFirstChar =
    isLoading && lastMsg?.role === "tutor" && lastMsg?.content === "";

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)]">
      {/* Header with concept selector */}
      <div className="px-4 py-3 border-b border-gray-100 bg-white flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-brand-600 shrink-0" />
        <select
          value={conceptId}
          onChange={(e) => {
            setConceptId(e.target.value);
            clearMessages();
          }}
          className="font-medium text-gray-900 text-sm border-none bg-transparent cursor-pointer focus:outline-none flex-1 min-w-0"
        >
          {concepts.length === 0 && <option value={conceptId}>{currentConceptName}</option>}
          {concepts.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        <span className="ml-auto text-xs text-gray-400 shrink-0">BrainGuide</span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center text-gray-400 text-sm mt-12"
          >
            <div className="text-3xl mb-3">🌱</div>
            <p>Ask me anything about <strong>{currentConceptName}</strong>.</p>
            <p className="text-xs mt-1">I'll guide you to discover it yourself.</p>
          </motion.div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.role === "student" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "student"
                    ? "bg-brand-600 text-white rounded-br-sm"
                    : "bg-white border border-gray-100 text-gray-800 rounded-bl-sm shadow-sm"
                }`}
              >
                {msg.content || (
                  /* Show dots only while waiting for the very first character */
                  isWaitingForFirstChar && i === messages.length - 1 ? (
                    <div className="flex gap-1 py-1">
                      {[0, 1, 2].map((j) => (
                        <motion.div
                          key={j}
                          className="w-2 h-2 bg-gray-300 rounded-full"
                          animate={{ y: [0, -4, 0] }}
                          transition={{ repeat: Infinity, duration: 0.8, delay: j * 0.2 }}
                        />
                      ))}
                    </div>
                  ) : null
                )}
                {msg.focus_cue && (
                  <div className="mt-2 pt-2 border-t border-brand-100 text-xs text-brand-200 italic">
                    {msg.focus_cue}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-4 bg-white border-t border-gray-100">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder="Share your thinking..."
            className="input flex-1"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="btn-primary px-3 py-3"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
