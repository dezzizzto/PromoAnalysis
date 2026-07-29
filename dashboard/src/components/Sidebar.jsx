import { useState } from "react";

const nav = [
  { id: "dashboard", label: "Dashboard", icon: "LayoutDashboard" },
  { id: "pipeline", label: "Pipeline", icon: "Container" },
  { id: "whatsapp", label: "WhatsApp", icon: "MessageCircle" },
  { id: "telegram", label: "Telegram", icon: "Send" },
  { id: "reports", label: "Relatórios", icon: "BarChart3" },
  { id: "alerts", label: "Alertas", icon: "Bell" },
  { id: "settings", label: "Configurações", icon: "Settings" },
];

const iconMap = {
  LayoutDashboard: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="7" height="9" x="3" y="3"/><rect width="7" height="5" x="14" y="3"/><rect width="7" height="9" x="14" y="12"/><rect width="7" height="5" x="3" y="16"/></svg>
  ),
  Container: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
  ),
  MessageCircle: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
  ),
  Send: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 2 11 13"/><path d="m22 2-7 20-4-9-9-4Z"/></svg>
  ),
  BarChart3: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
  ),
  Bell: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 4 9 4 9H2s4-2 4-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
  ),
  Settings: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
  ),
};

export default function Sidebar({ active, onChange }) {
  return (
    <aside className="w-56 border-r border-surface-800 h-screen flex flex-col bg-surface-950/80 backdrop-blur-sm fixed left-0 top-0 z-40">
      <div className="flex items-center gap-3 px-5 pt-6 pb-4">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-flame-500 to-flame-400 flex items-center justify-center shadow-lg shadow-flame-500/30">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M12 2c1.2 3-1.6 4.2-1.6 7 0 1.5 1 2.5 2.3 2.5 1.7 0 2.5-1.4 2.3-3 2 1.8 3 4 3 6.2C18 18.8 15.4 22 12 22s-6-3-6-6.8c0-3.6 2.2-6 3.3-8.4C10 5 11 3.3 12 2Z" fill="#16110a"/>
          </svg>
        </div>
        <div>
          <h1 className="font-display font-semibold text-sm">PromoAnalysis</h1>
          <p className="text-[11px] text-surface-400">Painel de controle</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-2 space-y-1">
        {nav.map((item) => {
          const Icon = iconMap[item.icon];
          const isActive = active === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onChange(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
                isActive
                  ? "bg-flame-500/10 text-flame-400 font-medium"
                  : "text-surface-400 hover:text-surface-200 hover:bg-surface-800/50"
              }`}
            >
              <span className={isActive ? "text-flame-400" : "text-surface-500"}>{Icon()}</span>
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="px-4 pb-6">
        <div className="rounded-lg bg-surface-900 border border-surface-800 p-3">
          <p className="text-[11px] text-surface-400">v8.0</p>
          <p className="text-[11px] text-surface-500">Painel de Controle</p>
        </div>
      </div>
    </aside>
  );
}
