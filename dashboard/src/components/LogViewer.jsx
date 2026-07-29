import { useEffect, useRef } from "react";

const levelColors = {
  INFO: "text-blue-400",
  WARNING: "text-yellow-400",
  ERROR: "text-red-400",
  SUCCESS: "text-emerald-400",
};

function parseLogs(text) {
  if (!text || text === "(sem execuções ainda)") return [{ level: "INFO", text: text || "Aguardando logs..." }];
  return text.split("\n").filter(Boolean).map((line) => {
    const match = line.match(/\b(INFO|WARNING|ERROR|SUCCESS)\b/i);
    const level = match ? match[1].toUpperCase() : "INFO";
    return { level, text: line };
  });
}

export default function LogViewer({ logs }) {
  const ref = useRef(null);
  const entries = parseLogs(logs?.conteudo);

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [logs]);

  return (
    <div className="bg-surface-900 border border-surface-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-surface-400"><path d="M4 4h16v2H4V4Zm0 5h10v2H4V9Zm0 5h16v2H4v-2Zm0 5h10v2H4v-2Z"/></svg>
          Log da Execução
        </h3>
      </div>
      <div ref={ref} className="bg-surface-950 rounded-lg p-3 h-[260px] overflow-y-auto font-mono text-xs space-y-0.5">
        {entries.map((e, i) => (
          <div key={i} className="leading-relaxed">
            <span className={`font-semibold ${levelColors[e.level] || "text-surface-400"}`}>
              {e.level.padEnd(7)}
            </span>
            <span className="text-surface-400">{e.text.slice(e.text.toUpperCase().indexOf(e.level) + e.level.length)}</span>
          </div>
        ))}
      </div>
      <div className="flex gap-2 mt-3">
        {["ALL", "INFO", "SUCCESS", "WARNING", "ERROR"].map((f) => (
          <button key={f} className="px-2.5 py-1 rounded text-[10px] font-medium bg-surface-800 text-surface-400 hover:text-surface-200 transition-colors">
            {f}
          </button>
        ))}
      </div>
    </div>
  );
}
