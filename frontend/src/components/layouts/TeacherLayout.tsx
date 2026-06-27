import { Outlet } from "react-router-dom";
import { GraduationCap } from "lucide-react";

export default function TeacherLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-100 px-6 py-4 flex items-center gap-3">
        <GraduationCap className="w-6 h-6 text-brand-600" />
        <span className="font-semibold text-gray-900">BrainEcosystem — Teacher</span>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
