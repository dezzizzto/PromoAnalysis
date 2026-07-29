import { useEffect, useState } from "react";
import { cn } from "../lib/utils";

function AnimatedNumber({ value, duration = 800 }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    if (value === display) return;
    const start = display;
    const diff = value - start;
    const startTime = performance.now();
    const tick = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      setDisplay(Math.round(start + diff * progress));
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [value]);
  return <>{display.toLocaleString("pt-BR")}</>;
}

export default function StatCard({ label, value, icon, trend, flame = false, format, subtitle }) {
  const Icon = icon;
  return (
    <div className="bg-surface-900 border border-surface-800 rounded-xl p-4 relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-flame-500/3 to-transparent rounded-full -translate-y-1/2 translate-x-1/2" />
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs font-medium text-surface-400 uppercase tracking-wider">{label}</span>
        {Icon && (
          <span className="w-8 h-8 rounded-lg bg-flame-500/10 flex items-center justify-center text-flame-400">
            {Icon()}
          </span>
        )}
      </div>
      {subtitle ? (
        <div className={cn("font-display text-lg font-bold", flame && "text-transparent bg-clip-text bg-gradient-to-r from-flame-400 to-flame-500")}>
          {subtitle}
        </div>
      ) : (
        <div className={cn("font-display text-2xl font-bold", flame && "text-transparent bg-clip-text bg-gradient-to-r from-flame-400 to-flame-500")}>
          {format === "percent" ? (
            <>{value ?? "—"}%</>
          ) : (
            value != null ? <AnimatedNumber value={value} /> : "—"
          )}
        </div>
      )}
      {trend && (
        <p className="text-xs text-surface-500 mt-1 flex items-center gap-1">
          <span className={trend.startsWith("+") ? "text-emerald-400" : "text-red-400"}>{trend}</span>
          Últimas 24 horas
        </p>
      )}
    </div>
  );
}
