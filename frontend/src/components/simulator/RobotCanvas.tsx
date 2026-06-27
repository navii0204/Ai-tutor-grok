import { useEffect, useRef } from "react";

interface Props {
  gridSize: number;
  robotPos: { x: number; y: number };
  facing: string;
  targetPos: { x: number; y: number };
}

const FACING_ANGLES: Record<string, number> = {
  east: 0,
  south: Math.PI / 2,
  west: Math.PI,
  north: -Math.PI / 2,
};

export default function RobotCanvas({ gridSize, robotPos, facing, targetPos }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const CANVAS_SIZE = 300;
  const CELL = CANVAS_SIZE / gridSize;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);

    // Grid
    ctx.strokeStyle = "#e5e7eb";
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= gridSize; i++) {
      ctx.beginPath();
      ctx.moveTo(i * CELL, 0);
      ctx.lineTo(i * CELL, CANVAS_SIZE);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, i * CELL);
      ctx.lineTo(CANVAS_SIZE, i * CELL);
      ctx.stroke();
    }

    // Target
    ctx.fillStyle = "#d1fae5";
    ctx.fillRect(targetPos.x * CELL + 1, targetPos.y * CELL + 1, CELL - 2, CELL - 2);
    ctx.fillStyle = "#065f46";
    ctx.font = `${CELL * 0.55}px sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("⭐", targetPos.x * CELL + CELL / 2, targetPos.y * CELL + CELL / 2);

    // Robot
    const rx = robotPos.x * CELL + CELL / 2;
    const ry = robotPos.y * CELL + CELL / 2;
    const angle = FACING_ANGLES[facing] ?? 0;

    ctx.save();
    ctx.translate(rx, ry);
    ctx.rotate(angle);

    ctx.fillStyle = "#16a34a";
    ctx.beginPath();
    ctx.roundRect(-CELL * 0.35, -CELL * 0.35, CELL * 0.7, CELL * 0.7, 4);
    ctx.fill();

    // Direction arrow
    ctx.fillStyle = "white";
    ctx.beginPath();
    ctx.moveTo(CELL * 0.28, 0);
    ctx.lineTo(CELL * 0.08, -CELL * 0.15);
    ctx.lineTo(CELL * 0.08, CELL * 0.15);
    ctx.closePath();
    ctx.fill();

    ctx.restore();
  }, [gridSize, robotPos, facing, targetPos, CELL]);

  return (
    <canvas
      ref={canvasRef}
      width={CANVAS_SIZE}
      height={CANVAS_SIZE}
      className="w-full rounded-xl border border-gray-100"
      style={{ imageRendering: "pixelated" }}
    />
  );
}
