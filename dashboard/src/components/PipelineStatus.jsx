import { cn } from "../lib/utils";

const steps = [
  { id: "extract", label: "Coletando", desc: "Extraindo mensagens dos grupos" },
  { id: "filter", label: "Filtrando", desc: "Identificando promoções" },
  { id: "compare", label: "Comparando", desc: "Verificando preços e descontos" },
  { id: "sheets", label: "Google Sheets", desc: "Enviando para a planilha" },
  { id: "alert", label: "Alertas", desc: "Verificando descontos altos" },
];

export default function PipelineStatus({ running }) {
  const activeIndex = running ? Math.floor((Date.now() / 2000) % steps.length) : -1;
  return (
    <div className="bg-surface-900 border border-surface-800 rounded-xl p-5">
      <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-surface-400"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        Pipeline
      </h3>
      <div className="relative">
        {steps.map((step, i) => {
          const isActive = i === activeIndex;
          const isDone = i < activeIndex;
          return (
            <div key={step.id} className="flex items-start gap-4 pb-5 last:pb-0 relative">
              {i < steps.length - 1 && (
                <div className={cn("absolute left-[11px] top-[26px] w-[2px] h-[calc(100%-12px)] transition-colors", isDone ? "bg-flame-500" : "bg-surface-800")} />
              )}
              <div className={cn(
                "w-[24px] h-[24px] rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all z-10",
                isActive && "border-flame-400 bg-flame-500/20 shadow-lg shadow-flame-500/20",
                isDone && "border-flame-500 bg-flame-500",
                !isActive && !isDone && "border-surface-700 bg-surface-800"
              )}>
                {isDone ? (
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#16110a" strokeWidth="3"><path d="M20 6 9 17l-5-5"/></svg>
                ) : isActive ? (
                  <span className="w-[6px] h-[6px] rounded-full bg-flame-400 animate-pulse" />
                ) : (
                  <span className="w-[6px] h-[6px] rounded-full bg-surface-600" />
                )}
              </div>
              <div className="flex-1 min-w-0 pt-0.5">
                <p className={cn("text-sm font-medium", isActive ? "text-flame-400" : isDone ? "text-surface-200" : "text-surface-400")}>
                  {step.label}
                </p>
                <p className="text-xs text-surface-500 mt-0.5">{step.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
