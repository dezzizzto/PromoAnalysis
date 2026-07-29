import { useCallback } from "react";
import { usePolling } from "../hooks/useApi";
import { api } from "../services/api";
import Header from "../components/Header";
import StatCard from "../components/StatCard";
import PipelineStatus from "../components/PipelineStatus";
import SourceList from "../components/SourceList";
import QuickActions from "../components/QuickActions";
import LogViewer from "../components/LogViewer";
import ExtractionChart from "../components/Charts/ExtractionChart";

export default function Dashboard() {
  const { data: stats, refetch: refetchStats } = usePolling(api.stats, 5000);
  const { data: status, refetch: refetchStatus } = usePolling(api.status, 2000);
  const { data: logs } = usePolling(api.logs, 3000);
  const { data: config } = usePolling(api.config, 10000);
  const { data: promocoes } = usePolling(api.promocoes, 30000);

  const handleRun = useCallback(async () => {
    await api.run();
    refetchStatus();
  }, [refetchStatus]);

  return (
    <div className="space-y-6">
      <Header status={status} />

      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Promoções Encontradas"
          value={stats?.total_promocoes ?? 0}
          flame
          trend="+12%"
          icon={() => (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2c1.2 3-1.6 4.2-1.6 7 0 1.5 1 2.5 2.3 2.5 1.7 0 2.5-1.4 2.3-3 2 1.8 3 4 3 6.2C18 18.8 15.4 22 12 22s-6-3-6-6.8c0-3.6 2.2-6 3.3-8.4C10 5 11 3.3 12 2Z"/></svg>
          )}
        />
        <StatCard
          label="Fontes Monitoradas"
          value={stats?.total_fontes ?? 0}
          icon={() => (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
          )}
        />
        <StatCard
          label="Limite de Alerta"
          value={stats?.limite_desconto}
          format="percent"
          icon={() => (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 8a6 6 0 0 1 12 0c0 7 4 9 4 9H2s4-2 4-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
          )}
        />
        <StatCard
          label="Última Execução"
          value={0}
          subtitle={stats?.ultima_execucao || "—"}
          icon={() => (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          )}
          flame
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <PipelineStatus running={status?.rodando} />
        <SourceList config={config} />
        <QuickActions onRun={handleRun} running={status?.rodando} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <ExtractionChart data={promocoes?.por_dia} lojas={promocoes?.por_loja} />
        <LogViewer logs={logs} />
      </div>
    </div>
  );
}
