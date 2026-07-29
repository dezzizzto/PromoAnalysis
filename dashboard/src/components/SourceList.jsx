const icons = {
  whatsapp: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.5 2 2 6.5 2 12c0 1.9.5 3.7 1.5 5.3L2 22l4.9-1.3A10 10 0 0 0 12 22c5.5 0 10-4.5 10-10S17.5 2 12 2Z"/></svg>
  ),
  telegram: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2Zm4.9 7.2-1.6 7.6c-.1.5-.4.7-.9.4l-2.5-1.8-1.2 1.1c-.1.1-.3.2-.5.2l.2-2.6 4.7-4.3c.2-.2 0-.3-.3-.1l-5.8 3.7-2.5-.8c-.5-.2-.5-.5.1-.7l9.9-3.8c.4-.2.8.1.7.6Z"/></svg>
  ),
};

const colors = {
  whatsapp: "text-emerald-400",
  telegram: "text-sky-400",
};

export default function SourceList({ config }) {
  const groups = [
    ...(config?.whatsapp_grupos || []).map((n) => ({ name: n, type: "whatsapp" })),
    ...(config?.whatsapp_canais || []).map((n) => ({ name: n, type: "whatsapp" })),
    ...(config?.telegram_grupos_canais || []).map((n) => ({ name: n, type: "telegram" })),
  ];
  return (
    <div className="bg-surface-900 border border-surface-800 rounded-xl p-5">
      <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-surface-400"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
        Fontes Monitoradas
      </h3>
      <div className="space-y-1.5 max-h-[260px] overflow-y-auto">
        {groups.length === 0 && <p className="text-xs text-surface-500">Nenhuma fonte configurada</p>}
        {groups.map((g, i) => {
          const Icon = icons[g.type];
          return (
            <div key={i} className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-surface-950/50">
              <span className={colors[g.type]}>{Icon()}</span>
              <span className="text-sm flex-1 truncate">{g.name}</span>
              <span className="text-[10px] text-surface-500 uppercase tracking-wider">{g.type === "whatsapp" ? "Grupo" : "Canal"}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
