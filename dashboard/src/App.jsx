import { useState } from "react";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";

export default function App() {
  const [page, setPage] = useState("dashboard");

  return (
    <div className="min-h-screen bg-surface-950">
      <Sidebar active={page} onChange={setPage} />
      <main className="ml-56 p-6">
        {page === "dashboard" && <Dashboard />}
      </main>
    </div>
  );
}
