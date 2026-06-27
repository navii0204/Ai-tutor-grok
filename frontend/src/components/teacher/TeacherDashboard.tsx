import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { getClassroomInsights } from "../../lib/api";

export default function TeacherDashboard() {
  const [grade, setGrade] = useState("7");
  const tenantId = "demo-school-001";

  const { data: insights, isLoading } = useQuery({
    queryKey: ["classroom-insights", tenantId, grade],
    queryFn: () => getClassroomInsights(tenantId, grade),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Classroom Insights</h1>
        <select
          value={grade}
          onChange={(e) => setGrade(e.target.value)}
          className="border border-gray-200 rounded-xl px-3 py-2 text-sm"
        >
          {["6", "7", "8"].map((g) => (
            <option key={g} value={g}>Grade {g}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <div className="text-gray-400 animate-pulse">Loading insights...</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          <div className="card">
            <h2 className="text-sm font-semibold text-gray-500 mb-3">Students Needing Support</h2>
            {insights?.at_risk_students?.length === 0 ? (
              <p className="text-sm text-gray-400">All students on track 🎉</p>
            ) : (
              <ul className="space-y-1">
                {insights?.at_risk_students?.map((id: string) => (
                  <li key={id} className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-1.5">{id}</li>
                ))}
              </ul>
            )}
          </div>

          <div className="card">
            <h2 className="text-sm font-semibold text-gray-500 mb-3">Weak Concepts This Week</h2>
            <ul className="space-y-1">
              {insights?.weak_concepts?.map((c: string) => (
                <li key={c} className="text-sm text-orange-700 bg-orange-50 rounded-lg px-3 py-1.5">
                  {c.replace(/_/g, " ")}
                </li>
              ))}
            </ul>
          </div>

          <div className="card md:col-span-2">
            <h2 className="text-sm font-semibold text-gray-500 mb-3">Class Mastery Averages</h2>
            <div className="space-y-2">
              {Object.entries(insights?.class_averages ?? {}).map(([concept, avg]) => (
                <div key={concept}>
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span>{concept.replace(/_/g, " ")}</span>
                    <span>{Math.round((avg as number) * 100)}%</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(avg as number) * 100}%` }}
                      className={`h-full rounded-full ${
                        (avg as number) > 0.7 ? "bg-brand-500" : (avg as number) > 0.4 ? "bg-warm-500" : "bg-red-400"
                      }`}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
