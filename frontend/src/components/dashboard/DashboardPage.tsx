import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Flame, Star, Clock, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getDailyPlan } from "../../lib/api";
import { useSessionStore } from "../../stores/sessionStore";

export default function DashboardPage() {
  const studentId = useSessionStore((s) => s.studentId);
  const setConceptId = useSessionStore((s) => s.setConceptId);
  const navigate = useNavigate();

  const { data: plan, isLoading } = useQuery({
    queryKey: ["daily-plan", studentId],
    queryFn: () => getDailyPlan(studentId),
    enabled: !!studentId,
  });

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[50vh]">
        <div className="text-gray-400 animate-pulse">Loading your plan...</div>
      </div>
    );
  }

  return (
    <div className="p-4 max-w-lg mx-auto space-y-4">
      {/* Focus Cue */}
      {plan?.focus_cue && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-warm-50 border border-warm-100 rounded-2xl p-4 text-sm text-warm-700 italic"
        >
          {plan.focus_cue}
        </motion.div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-3">
        <div className="card text-center">
          <Flame className="w-5 h-5 text-orange-500 mx-auto mb-1" />
          <div className="text-2xl font-bold text-gray-900">{plan?.streak_days ?? 0}</div>
          <div className="text-xs text-gray-500">Day streak</div>
        </div>
        <div className="card text-center">
          <Star className="w-5 h-5 text-brand-500 mx-auto mb-1" />
          <div className="text-2xl font-bold text-gray-900">
            {Math.round((plan?.weekly_goal_progress ?? 0) * 100)}%
          </div>
          <div className="text-xs text-gray-500">Week goal</div>
        </div>
        <div className="card text-center">
          <Clock className="w-5 h-5 text-purple-500 mx-auto mb-1" />
          <div className="text-2xl font-bold text-gray-900">
            {plan?.activities?.reduce((s: number, a: any) => s + a.estimated_minutes, 0) ?? 0}
          </div>
          <div className="text-xs text-gray-500">min today</div>
        </div>
      </div>

      {/* Motivational message */}
      {plan?.motivational_message && (
        <div className="text-sm text-gray-600 px-1">{plan.motivational_message}</div>
      )}

      {/* Today's activities */}
      <div className="space-y-2">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide px-1">Today's plan</h2>
        {plan?.activities?.map((activity: any, i: number) => (
          <motion.button
            key={i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            onClick={() => {
              if (activity.activity_type !== "reflection") {
                setConceptId(activity.concept_id);
                navigate(
                  activity.activity_type === "simulator"
                    ? "/student/simulator/robot_sim"
                    : "/student/chat"
                );
              }
            }}
            className="card w-full text-left flex items-center gap-3 hover:bg-gray-50 transition-colors cursor-pointer group"
          >
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg shrink-0 ${
                activity.activity_type === "review"
                  ? "bg-blue-50"
                  : activity.activity_type === "simulator"
                  ? "bg-purple-50"
                  : activity.activity_type === "reflection"
                  ? "bg-green-50"
                  : "bg-warm-50"
              }`}
            >
              {activity.activity_type === "review" ? "🔄"
                : activity.activity_type === "simulator" ? "🤖"
                : activity.activity_type === "reflection" ? "🌿"
                : "💬"}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-medium text-gray-900 truncate">{activity.concept_name}</div>
              <div className="text-xs text-gray-500">{activity.estimated_minutes} min · {activity.reason}</div>
            </div>
            <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors shrink-0" />
          </motion.button>
        ))}
      </div>

      {/* Reflection prompt */}
      {plan?.reflection_prompt && (
        <div className="bg-brand-50 border border-brand-100 rounded-2xl p-4 text-sm text-brand-700">
          <span className="font-medium">Reflect: </span>{plan.reflection_prompt}
        </div>
      )}
    </div>
  );
}
