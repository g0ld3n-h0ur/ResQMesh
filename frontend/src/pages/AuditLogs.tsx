import React, { useState } from "react";
import {
  ShieldCheck,
  Search,
  ShieldAlert
} from "lucide-react";

interface AuditEntry {
  id: string;
  actor: string;
  role: string;
  organization: string;
  action: string;
  entity: string;
  entity_id: string;
  timestamp: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  prev_state: string;
  new_state: string;
}

interface AnomalyEntry {
  id: string;
  anomaly_type: string;
  severity: "HIGH" | "CRITICAL" | "MEDIUM";
  explanation: string;
  entity: string;
  timestamp: string;
  status: "OPEN" | "INVESTIGATING" | "RESOLVED";
}

const AUDIT_LOGS: AuditEntry[] = [
  {
    id: "AUD-1092",
    actor: "gov.admin@tn.gov.in",
    role: "Government",
    organization: "Tamil Nadu State Disaster Relief",
    action: "ALLOCATE_RESOURCE",
    entity: "Resource",
    entity_id: "RES-WATER-99",
    timestamp: "2026-08-08T09:12:00Z",
    severity: "INFO",
    prev_state: "AVAILABLE (5000L)",
    new_state: "ALLOCATED (3000L to Zone B)",
  },
  {
    id: "AUD-1093",
    actor: "ngo.lead@disasteraid.org",
    role: "NGO",
    organization: "DisasterAid India",
    action: "ASSIGN_VOLUNTEER",
    entity: "VolunteerAssignment",
    entity_id: "ASN-VOL-301",
    timestamp: "2026-08-08T08:45:00Z",
    severity: "INFO",
    prev_state: "PENDING",
    new_state: "ASSIGNED (Medical Triage Unit)",
  },
  {
    id: "AUD-1094",
    actor: "hospital.admin@apollo.in",
    role: "Hospital",
    organization: "Apollo Emergency Center",
    action: "UPDATE_CAPACITY",
    entity: "HospitalCapacity",
    entity_id: "HOSP-002",
    timestamp: "2026-08-08T08:30:00Z",
    severity: "WARNING",
    prev_state: "ICU Available: 12",
    new_state: "ICU Available: 2 (CRITICAL CAP)",
  },
  {
    id: "AUD-1095",
    actor: "system_rule_engine",
    role: "System",
    organization: "ResQMesh Automated Audit",
    action: "FLAG_ANOMALY",
    entity: "DeliveryManifest",
    entity_id: "DEL-901",
    timestamp: "2026-08-08T08:31:00Z",
    severity: "CRITICAL",
    prev_state: "Dispatched: 1000",
    new_state: "Received: 980 (Discrepancy 20)",
  },
];

const ANOMALIES: AnomalyEntry[] = [
  {
    id: "ANO-001",
    anomaly_type: "DISPATCHED > AVAILABLE",
    severity: "CRITICAL",
    explanation: "Resource allocation request for 6000L drinking water exceeds available warehouse inventory (5000L).",
    entity: "Resource RES-WATER-99",
    timestamp: "2026-08-08T09:10:00Z",
    status: "OPEN",
  },
  {
    id: "ANO-002",
    anomaly_type: "DELIVERED > DISPATCHED",
    severity: "HIGH",
    explanation: "Receipt manifest recorded 550 blankets delivered when dispatched manifest logged 500.",
    entity: "Delivery DEL-882",
    timestamp: "2026-08-08T07:40:00Z",
    status: "INVESTIGATING",
  },
  {
    id: "ANO-003",
    anomaly_type: "INVALID STATUS TRANSITION",
    severity: "MEDIUM",
    explanation: "Incident status transitioned directly from UNVERIFIED to RESOLVED skipping IN_PROGRESS.",
    entity: "EmergencyReport REP-441",
    timestamp: "2026-08-08T06:15:00Z",
    status: "RESOLVED",
  },
];

export const AuditLogs: React.FC = () => {
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState<"logs" | "anomalies">("logs");

  const filteredLogs = AUDIT_LOGS.filter(
    (log) =>
      log.actor.toLowerCase().includes(search.toLowerCase()) ||
      log.action.toLowerCase().includes(search.toLowerCase()) ||
      log.organization.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl text-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-600/30 shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-extrabold tracking-tight">Audit Trail & Rule-Based Anomaly Detection</h2>
              <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                READ-ONLY IMMUTABLE LEDGER
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Complete administrative audit trail of all allocation actions, capacity updates, and automated fraud/anomaly checks.
            </p>
          </div>
        </div>

        {/* Tab Selector */}
        <div className="flex bg-slate-950 p-1.5 rounded-2xl border border-slate-800 space-x-1">
          <button
            onClick={() => setActiveTab("logs")}
            className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all ${
              activeTab === "logs"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Audit Trail Logs
          </button>
          <button
            onClick={() => setActiveTab("anomalies")}
            className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all ${
              activeTab === "anomalies"
                ? "bg-rose-600 text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Rule-Based Anomaly Alerts ({ANOMALIES.length})
          </button>
        </div>
      </div>

      {activeTab === "logs" ? (
        <div className="bg-white border border-slate-200 rounded-3xl shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h3 className="text-base font-bold text-slate-800">Immutable System Event Logs</h3>
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Filter by actor, action, org..."
                className="pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] uppercase font-bold text-slate-500 tracking-wider">
                  <th className="py-3 px-4">Log Ref</th>
                  <th className="py-3 px-4">Actor & Role</th>
                  <th className="py-3 px-4">Organization</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Entity</th>
                  <th className="py-3 px-4">State Transition</th>
                  <th className="py-3 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-700">{log.id}</td>
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-800">{log.actor}</div>
                      <span className="text-[10px] text-indigo-600 font-medium">{log.role}</span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">{log.organization}</td>
                    <td className="py-3.5 px-4 font-bold text-slate-800">{log.action}</td>
                    <td className="py-3.5 px-4 font-mono text-slate-600">{log.entity_id}</td>
                    <td className="py-3.5 px-4">
                      <div className="text-[11px] text-slate-400 line-through">{log.prev_state}</div>
                      <div className="text-xs font-semibold text-indigo-700">{log.new_state}</div>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-500">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Anomalies Dashboard */
        <div className="space-y-4">
          <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-2xl text-amber-900 text-xs flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
            <span>
              <strong>Rule-Based Anomaly Detection Engine</strong> evaluates inventory thresholds, delivery receipts, and state transitions for discrepancies.
            </span>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {ANOMALIES.map((ano) => (
              <div key={ano.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <span className={`px-2.5 py-0.5 rounded text-[10px] uppercase font-bold border ${
                    ano.severity === "CRITICAL"
                      ? "bg-rose-50 text-rose-700 border-rose-200"
                      : "bg-amber-50 text-amber-700 border-amber-200"
                  }`}>
                    {ano.severity} SEVERITY
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">{ano.id}</span>
                </div>
                <h4 className="font-bold text-slate-800 text-sm">{ano.anomaly_type}</h4>
                <p className="text-xs text-slate-600 leading-relaxed">{ano.explanation}</p>
                <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="font-mono text-slate-500 text-[11px]">{ano.entity}</span>
                  <span className="font-bold text-indigo-600">{ano.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
