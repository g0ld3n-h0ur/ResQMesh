import React, { useState } from "react";

const RESPONSE_SLA_DATA = [
  { metric: "Triage / AI Classification", target_mins: 2, actual_mins: 1.4, status: "MET" },
  { metric: "Team Assignment", target_mins: 15, actual_mins: 12.0, status: "MET" },
  { metric: "Warehouse Dispatch", target_mins: 30, actual_mins: 28.5, status: "MET" },
  { metric: "First Unit On-Site", target_mins: 45, actual_mins: 52.0, status: "BREACHED" },
  { metric: "Full Incident Resolution", target_mins: 240, actual_mins: 210.0, status: "MET" },
];

export const SLAAnalyticsAAR: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"sla" | "aar">("sla");

  return (
    <div className="space-y-4 font-sans text-[#172033]">
      
      {/* Header */}
      <div className="bg-white border border-[#E4E7EC] rounded-md p-3.5 flex items-center justify-between">
        <div>
          <h1 className="text-sm font-bold text-[#172033]">SLA Analytics & After-Action Review (AAR)</h1>
          <p className="text-[11px] text-[#667085]">
            Operational response SLA benchmarks and post-disaster evaluation reports.
          </p>
        </div>

        <div className="flex space-x-1 bg-[#F7F8FA] p-1 rounded border border-[#E4E7EC] text-xs font-semibold">
          <button
            onClick={() => setActiveTab("sla")}
            className={`px-3 py-1 rounded transition-colors ${
              activeTab === "sla" ? "bg-white text-blue-700 shadow-2xs font-bold" : "text-[#667085]"
            }`}
          >
            Response SLAs
          </button>
          <button
            onClick={() => setActiveTab("aar")}
            className={`px-3 py-1 rounded transition-colors ${
              activeTab === "aar" ? "bg-white text-blue-700 shadow-2xs font-bold" : "text-[#667085]"
            }`}
          >
            After-Action Review
          </button>
        </div>
      </div>

      {activeTab === "sla" ? (
        <div className="bg-white border border-[#E4E7EC] rounded-md overflow-hidden">
          <div className="p-3 border-b border-[#E4E7EC] bg-[#F7F8FA] flex items-center justify-between text-xs">
            <span className="font-bold text-[#172033]">Response Milestone SLA Benchmarks</span>
            <span className="text-[10px] text-[#667085]">TARGET vs ACTUAL</span>
          </div>

          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-[#E4E7EC] text-[10px] uppercase font-bold text-[#667085]">
                <th className="py-2 px-3">Milestone Metric</th>
                <th className="py-2 px-3 text-right">Target (Mins)</th>
                <th className="py-2 px-3 text-right">Actual (Mins)</th>
                <th className="py-2 px-3">Compliance Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E4E7EC]">
              {RESPONSE_SLA_DATA.map((row) => (
                <tr key={row.metric} className="hover:bg-slate-50">
                  <td className="py-2 px-3 font-semibold text-[#172033]">{row.metric}</td>
                  <td className="py-2 px-3 text-right font-mono text-[#667085]">{row.target_mins}</td>
                  <td className="py-2 px-3 text-right font-mono font-bold text-[#172033]">{row.actual_mins}</td>
                  <td className="py-2 px-3">
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                      row.status === "MET"
                        ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                        : "bg-red-50 text-red-800 border border-red-200"
                    }`}>
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-white border border-[#E4E7EC] rounded-md p-4 space-y-3 text-xs">
          <div className="border-b border-[#E4E7EC] pb-2 font-bold text-[#172033]">
            After-Action Review: Incident DIS-2024-001 (Chennai Flood)
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            <div className="p-3 bg-slate-50 border border-[#E4E7EC] rounded space-y-1">
              <span className="font-bold text-[#172033] text-xs">1. Response Performance</span>
              <p className="text-[11px] text-[#667085]">Average triage time 1.4 minutes vs target 2.0 minutes. 98.2% incident resolution rate.</p>
            </div>

            <div className="p-3 bg-slate-50 border border-[#E4E7EC] rounded space-y-1">
              <span className="font-bold text-[#172033] text-xs">2. Bottlenecks Identified</span>
              <p className="text-[11px] text-[#667085]">Submerged underpass caused 7-minute transit delay. ICU beds reached 98% capacity at peak hour.</p>
            </div>

            <div className="p-3 bg-slate-50 border border-[#E4E7EC] rounded space-y-1">
              <span className="font-bold text-[#172033] text-xs">3. Action Directives</span>
              <p className="text-[11px] text-[#667085]">Pre-position high-clearance rescue vehicles in Sector 2. Establish secondary field hospital at Sector 4.</p>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
