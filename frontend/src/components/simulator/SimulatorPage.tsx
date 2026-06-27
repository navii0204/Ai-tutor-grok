import { useState, useRef, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { RotateCcw, Play } from "lucide-react";
import { simulatorCommand } from "../../lib/api";
import { useSessionStore } from "../../stores/sessionStore";
import RobotCanvas from "./RobotCanvas";

const COMMANDS = [
  { cmd: "move_forward", label: "Move Forward", params: { steps: 1 } },
  { cmd: "turn_left", label: "Turn Left", params: {} },
  { cmd: "turn_right", label: "Turn Right", params: {} },
  { cmd: "pen_down", label: "Pen Down", params: {} },
  { cmd: "pen_up", label: "Pen Up", params: {} },
  { cmd: "sense_distance", label: "Sense Distance", params: {} },
];

interface SimState {
  robot_position: string;
  facing: string;
  steps_taken: number;
  obstacles_hit: number;
  grid_size: number;
  target: string;
}

export default function SimulatorPage() {
  const studentId = useSessionStore((s) => s.studentId);
  const [simState, setSimState] = useState<SimState | null>(null);
  const [events, setEvents] = useState<string[]>([]);
  const [message, setMessage] = useState<string>("");
  const [isComplete, setIsComplete] = useState(false);
  const [score, setScore] = useState<number | null>(null);

  const reset = useCallback(async () => {
    const res = await simulatorCommand({
      student_id: studentId,
      simulator_id: "robot_sim",
      command: "reset",
      config: { grid_size: 8, start_x: 0, start_y: 0, target: [7, 7] },
    });
    setSimState(res.state);
    setEvents([]);
    setMessage("Robot reset! Navigate to the target (7,7).");
    setIsComplete(false);
    setScore(null);
  }, [studentId]);

  useEffect(() => { reset(); }, [reset]);

  async function executeCommand(cmd: string, params: Record<string, unknown>) {
    if (isComplete) return;
    const res = await simulatorCommand({
      student_id: studentId,
      simulator_id: "robot_sim",
      command: cmd,
      params,
    });
    setSimState(res.state);
    setEvents(res.events ?? []);
    setMessage(res.message);
    if (res.is_complete) {
      setIsComplete(true);
      setScore(res.score);
    }
  }

  const robotPos = simState
    ? (() => {
        const m = simState.robot_position.match(/\((\d+),(\d+)\)/);
        return m ? { x: parseInt(m[1]), y: parseInt(m[2]) } : { x: 0, y: 0 };
      })()
    : { x: 0, y: 0 };

  const targetPos = simState
    ? (() => {
        const m = simState.target?.match(/\((\d+),\s*(\d+)\)/);
        return m ? { x: parseInt(m[1]), y: parseInt(m[2]) } : { x: 7, y: 7 };
      })()
    : { x: 7, y: 7 };

  return (
    <div className="p-4 max-w-lg mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-semibold text-gray-900">Robot Grid Lab</h1>
        <button onClick={reset} className="btn-secondary flex items-center gap-1 text-xs py-1.5 px-3">
          <RotateCcw className="w-3 h-3" /> Reset
        </button>
      </div>

      {/* Canvas */}
      <div className="card p-2">
        <RobotCanvas
          gridSize={simState?.grid_size ?? 8}
          robotPos={robotPos}
          facing={simState?.facing ?? "east"}
          targetPos={targetPos}
        />
      </div>

      {/* Status */}
      <div className="card text-sm space-y-1">
        <div className="flex justify-between text-gray-600">
          <span>Position: <strong>{simState?.robot_position}</strong></span>
          <span>Facing: <strong>{simState?.facing}</strong></span>
        </div>
        <div className="flex justify-between text-gray-600">
          <span>Steps: <strong>{simState?.steps_taken ?? 0}</strong></span>
          <span className={simState?.obstacles_hit ? "text-red-500" : ""}>
            Hits: <strong>{simState?.obstacles_hit ?? 0}</strong>
          </span>
        </div>
        {message && <div className="text-xs text-gray-500 italic pt-1">{message}</div>}
        {events.slice(-2).map((e, i) => (
          <div key={i} className="text-xs text-gray-400">{e}</div>
        ))}
      </div>

      {/* Completion */}
      {isComplete && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-brand-50 border border-brand-200 rounded-2xl p-4 text-center"
        >
          <div className="text-3xl mb-2">🎉</div>
          <div className="font-semibold text-brand-700">Target reached!</div>
          {score !== null && (
            <div className="text-sm text-brand-600 mt-1">Efficiency score: {Math.round(score * 100)}%</div>
          )}
        </motion.div>
      )}

      {/* Commands */}
      <div className="grid grid-cols-2 gap-2">
        {COMMANDS.map(({ cmd, label, params }) => (
          <button
            key={cmd}
            onClick={() => executeCommand(cmd, params)}
            disabled={isComplete}
            className="btn-secondary text-sm py-2.5"
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
