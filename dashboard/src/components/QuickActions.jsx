import { cn } from "../lib/utils";

const actions = [
  { id: "add-group", label: "Grupo", icon: "plus", variant: "primary" },
  { id: "add-channel", label: "Canal", icon: "plus", variant: "secondary" },
  { id: "run", label: "Executar", icon: "play", variant: "primary" },
  { id: "export", label: "Exportar CSV", icon: "download", variant: "secondary" },
  { id: "analytics", label: "Analytics", icon: "chart", variant: "secondary" },
  { id: "test-email", label: "Testar Email", icon: "mail", variant: "secondary" },
];

const icons = {
  plus: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 5v14M5 12h14"/></svg>
  ),
  play: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
  ),
  download: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
  ),
  chart: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18M7 16l4-4 4 4 5-5"/></svg>
  ),
  mail: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
  ),
};

export default function QuickActions({ onRun, running }) {
  return (
    <div className="bg-surface-900 border border-surface-800 rounded-xl p-5">
      <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-surface-400"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.8-3.8a1 1 0 0 0 0-1.4L19.5 2.7a1 1 0 0 0-1.4 0L14.7 6.3Z"/><path d="M20 11v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h5"/></svg>
        Ações Rápidas
      </h3>
      <div className="grid grid-cols-3 gap-2">
        {actions.map((a) => {
          const Icon = icons[a.icon];
          const isRun = a.id === "run";
          return (
            <button
              key={a.id}
              onClick={isRun ? onRun : undefined}
              disabled={isRun && running}
              className={cn(
                "flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-lg text-xs font-medium transition-all",
                a.variant === "primary"
                  ? "bg-gradient-to-r from-flame-500 to-flame-400 text-surface-950 shadow-md shadow-flame-500/20 hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed"
                  : "bg-surface-800 border border-surface-700 text-surface-300 hover:border-surface-600 hover:text-surface-100"
              )}
            >
              {Icon()}
              {a.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
