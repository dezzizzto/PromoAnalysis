import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export default function ExtractionChart({ data, lojas }) {
  const chartData = data?.length > 0 ? data : [];
  return (
    <div className="bg-surface-900 border border-surface-800 rounded-xl p-5">
      <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-surface-400"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
        Extrações (últimos 30 dias)
      </h3>
      {chartData.length === 0 ? (
        <p className="text-sm text-surface-500 text-center py-8">Aguardando dados...</p>
      ) : (
        <div className="h-[180px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262b38" vertical={false} />
              <XAxis dataKey="dia" axisLine={false} tickLine={false} tick={{ fill: "#8b93a3", fontSize: 11 }}
                tickFormatter={(v) => v?.slice(5) || ""} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: "#8b93a3", fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: "#151922", border: "1px solid #262b38", borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: "#eef0f3" }}
                formatter={(value) => [value.toLocaleString("pt-BR"), "Promoções"]}
              />
              <Line type="monotone" dataKey="total" stroke="#ff6b35" strokeWidth={2}
                dot={{ fill: "#ff6b35", r: 3 }} activeDot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      {lojas?.length > 0 && (
        <div className="mt-4 pt-4 border-t border-surface-800">
          <p className="text-xs text-surface-400 mb-2 font-medium uppercase tracking-wider">Por loja</p>
          <div className="grid grid-cols-2 gap-1.5">
            {lojas.slice(0, 6).map((l) => (
              <div key={l.loja} className="flex items-center gap-2 text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-flame-500 flex-shrink-0" />
                <span className="text-surface-300 flex-1 truncate">{l.loja}</span>
                <span className="text-surface-400 font-mono">{l.total.toLocaleString("pt-BR")}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
