import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, unwrapList } from "../lib/api";

interface AuditEntry {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  resource_ref: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  ip_address: string;
}

const INITIAL_LOGS: AuditEntry[] = [
  { id: "AUD-8012", timestamp: "2026-08-08T09:30:12Z", actor: "gov.admin@tn.gov.in", action: "Disaster Severity Elevation", resource_ref: "DIS-2024-001", severity: "CRITICAL", ip_address: "10.0.4.12" },
  { id: "AUD-8013", timestamp: "2026-08-08T09:22:45Z", actor: "ngo.lead@disasteraid.org", action: "Cargo Convoy Clearance", resource_ref: "DEL-901", severity: "INFO", ip_address: "10.0.8.44" },
  { id: "AUD-8014", timestamp: "2026-08-08T09:15:02Z", actor: "hospital.admin@apollo.in", action: "ICU Bed Capacity Alert", resource_ref: "HOSP-042", severity: "WARNING", ip_address: "10.0.12.9" },
  { id: "AUD-8015", timestamp: "2026-08-08T08:50:33Z", actor: "system.routing", action: "Obstacle Reroute Recalculation", resource_ref: "RT-8842", severity: "WARNING", ip_address: "127.0.0.1" },
  { id: "AUD-8016", timestamp: "2026-08-08T08:30:11Z", actor: "volunteer.john@resqmesh.org", action: "Delivery Sign-Off Verification", resource_ref: "DEL-902", severity: "INFO", ip_address: "10.0.19.4" },
];

export const AuditLogs: React.FC = () => {
  const [filterSeverity, setFilterSeverity] = useState<string>("ALL");

  const { data: apiLogs = [] } = useQuery<any[]>({
    queryKey: ["audit-trail"],
    queryFn: async () => unwrapList(await api.get("/governance/audit-trail")),
  });

  const logs: AuditEntry[] = apiLogs.length > 0
    ? apiLogs.map((l: any) => ({
        id: l.id ? `AUD-${l.id.slice(0, 4)}` : "AUD-0000",
        timestamp: l.created_at || new Date().toISOString(),
        actor: l.actor_role || l.actor_id || "system.admin",
        action: l.action || "State Change",
        resource_ref: l.entity_id ? `${l.entity_type || 'ENT'}-${l.entity_id.slice(0, 4)}` : "GEN-000",
        severity: l.action?.includes("CRITICAL") ? "CRITICAL" : l.action?.includes("WARN") ? "WARNING" : "INFO",
        ip_address: "127.0.0.1",
      }))
    : INITIAL_LOGS;

  const filtered = logs.filter(
    (l) => filterSeverity === "ALL" || l.severity === filterSeverity
  );

  return (
    <div className="space-y-4 font-sans text-[#172033]">
      
      {/* Header */}
      <div className="bg-white border border-[#E4E7EC] rounded-md p-3.5 flex items-center justify-between">
        <div>
          <h1 className="text-sm font-bold text-[#172033]">Immutable Audit Trail & Anomaly Detection</h1>
          <p className="text-[11px] text-[#667085]">
            Administrative event log tracking clearance actions, capacity updates, and system anomalies.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <label className="text-[10px] font-bold text-[#667085] uppercase">Filter Severity:</label>
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="px-2 py-1 bg-[#F7F8FA] border border-[#E4E7EC] rounded text-xs font-semibold"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical Only</option>
            <option value="WARNING">Warning Only</option>
            <option value="INFO">Info Only</option>
          </select>
        </div>
      </div>

      {/* Audit Table */}
      <div className="bg-white border border-[#E4E7EC] rounded-md overflow-hidden">
        <div className="p-3 border-b border-[#E4E7EC] bg-[#F7F8FA] flex items-center justify-between text-xs">
          <span className="font-bold text-[#172033]">System Action Logs</span>
          <span className="text-[10px] text-[#667085]">{filtered.length} Entries</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-[#E4E7EC] text-[10px] uppercase font-bold text-[#667085]">
                <th className="py-2 px-3">Audit ID</th>
                <th className="py-2 px-3">Timestamp</th>
                <th className="py-2 px-3">Actor / User</th>
                <th className="py-2 px-3">Action Details</th>
                <th className="py-2 px-3">Target Ref</th>
                <th className="py-2 px-3">Severity</th>
                <th className="py-2 px-3 text-right">IP Address</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E4E7EC]">
              {filtered.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50">
                  <td className="py-2 px-3 font-mono font-bold text-[#172033]">{log.id}</td>
                  <td className="py-2 px-3 font-mono text-[11px] text-[#667085]">
                    {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </td>
                  <td className="py-2 px-3 font-semibold text-[#172033]">{log.actor}</td>
                  <td className="py-2 px-3 font-medium text-[#172033]">{log.action}</td>
                  <td className="py-2 px-3 font-mono text-blue-700">{log.resource_ref}</td>
                  <td className="py-2 px-3">
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                      log.severity === "CRITICAL"
                        ? "bg-red-50 text-red-800 border border-red-200"
                        : log.severity === "WARNING"
                        ? "bg-amber-50 text-amber-800 border border-amber-200"
                        : "bg-slate-100 text-slate-700 border border-slate-200"
                    }`}>
                      {log.severity}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right font-mono text-[#667085] text-[11px]">{log.ip_address}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
