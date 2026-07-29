import { cn } from "../lib/utils";

export default function Header({ status }) {
  const isRunning = status?.rodando;
  return (
    <header className="flex items-center justify-between mb-6">
      <div>
        <h2 className="font-display text-xl font-semibold">Dashboard</h2>
        <p className="text-sm text-surface-400 mt-0.5">Visão geral do pipeline de extração</p>
      </div>
      <div className="flex items-center gap-4">
        <span
          className={cn(
            "inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-medium border transition-colors",
            isRunning
              ? "border-flame-500/40 bg-flame-500/10 text-flame-400"
              : "border-surface-700 bg-surface-900 text-surface-400"
          )}
        >
          <span
            className={cn(
              "w-2 h-2 rounded-full",
              isRunning ? "bg-flame-400 animate-pulse" : "bg-surface-500"
            )}
          />
          {isRunning ? "Pipeline em execução" : "Ocioso"}
        </span>
      </div>
    </header>
  );
}
