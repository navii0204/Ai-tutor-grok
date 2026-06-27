import { Outlet, NavLink } from "react-router-dom";
import { motion } from "framer-motion";
import { BookOpen, MessageCircle, Cpu, LayoutDashboard } from "lucide-react";

const navItems = [
  { to: "/student/dashboard", icon: LayoutDashboard, label: "Home" },
  { to: "/student/chat", icon: MessageCircle, label: "BrainGuide" },
  { to: "/student/simulator/robot_sim", icon: Cpu, label: "Lab" },
];

export default function StudentLayout() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Top bar */}
      <header className="bg-white border-b border-gray-100 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center">
          <BookOpen className="w-4 h-4 text-white" />
        </div>
        <span className="font-semibold text-gray-900">BrainEcosystem</span>
        <span className="ml-auto text-xs text-gray-400">Student</span>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-auto pb-20">
        <Outlet />
      </main>

      {/* Bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 flex">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center py-3 gap-1 text-xs font-medium transition-colors ${
                isActive ? "text-brand-600" : "text-gray-400 hover:text-gray-600"
              }`
            }
          >
            <Icon className="w-5 h-5" />
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
