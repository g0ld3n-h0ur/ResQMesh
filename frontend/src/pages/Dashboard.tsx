import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, unwrapDashboardHospitals, unwrapEnvelope, unwrapList } from "../lib/api";

interface SummaryData {
  disasters: { total: number; active: number; resolved: number };
  emergency_reports: { total: number; verified: number; unverified: number };
  resources: { total: number; available: number; allocated: number };
  shelters: { total: number; total_capacity: number; current_occupancy: number; available_spots: number };
  hospitals: { total: number; total_available_beds: number; total_icu_beds: number };
  users: { total_active: number; volunteers: number };
}

interface ShelterData {
  id: string;
  shelter_name: string;
  capacity: number;
  current_occupancy: number;
  district: string;
}

interface HospitalData {
  id: string;
  hospital_name: string;
  available_beds: number;
  icu_beds: number;
}

interface EmergencyReport {
  id: string;
  reporter_name: string;
  phone: string;
  disaster_type: string;
  address: string;
  description: string;
  is_verified: boolean;
  created_at: string;
}

const DEMO_INCIDENTS = [
  { id: "INC-24081", title: "Severe Coastal Flood Inundation", location: "Cuddalore Sector 2", affected: 2840, priority: "CRITICAL", status: "Active", updated: "4 min ago" },
  { id: "INC-24082", title: "ICU Primary Power Outage", location: "Tambaram Hospital", affected: 140, priority: "CRITICAL", status: "Active", updated: "12 min ago" },
  { id: "INC-24083", title: "Clean Water Supply Shortage", location: "Velachery Central", affected: 5200, priority: "HIGH", status: "Active", updated: "22 min ago" },
  { id: "INC-24084", title: "Submerged Highway Flyover", location: "Madipakkam Expressway", affected: 850, priority: "MEDIUM", status: "Active", updated: "35 min ago" },
  { id: "INC-24085", title: "Temporary Shelter Overcrowding", location: "Red Cross Field Unit", affected: 1200, priority: "HIGH", status: "Active", updated: "48 min ago" },
];

export const Dashboard: React.FC = () => {
  const [selectedIncident, setSelectedIncident] = useState("INC-24081");

  const { data: summary, refetch } = useQuery<SummaryData>({
    queryKey: ["dashboard-summary"],
    queryFn: async () => unwrapEnvelope<SummaryData>(await api.get("/dashboard/summary")),
    refetchInterval: 20_000,
  });

  const { data: shelters = [] } = useQuery<ShelterData[]>({
    queryKey: ["dashboard-shelters"],
    queryFn: async () => unwrapList<ShelterData>(await api.get("/dashboard/shelters")),
    refetchInterval: 20_000,
  });

  const { data: hospitals = [] } = useQuery<HospitalData[]>({
    queryKey: ["dashboard-hospitals"],
    queryFn: async () => unwrapDashboardHospitals<HospitalData>(await api.get("/dashboard/hospitals")),
    refetchInterval: 20_000,
  });

  const { data: reports = [] } = useQuery<EmergencyReport[]>({
    queryKey: ["emergency-reports"],
    queryFn: async () => unwrapList<EmergencyReport>(await api.get("/reports/")),
    refetchInterval: 20_000,
  });

  const activeIncidents = summary?.disasters?.active ?? 4;
  const criticalReports = summary?.emergency_reports?.unverified ?? 2;
  const totalAllocated = summary?.resources?.allocated ?? 18500;
  const availableShelters = summary?.shelters?.available_spots ?? 1240;

  return (
    <div className="space-y-4 font-sans text-[#172033]">
      
      {/* Page Header */}
      <div className="bg-white border border-[#E4E7EC] rounded-md p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-sm font-bold text-[#172033]">Command Center</h1>
            <span className="text-[#667085]">/</span>
            <span className="text-xs font-semibold text-[#667085]">Tamil Nadu Response Network</span>
          </div>
          <p className="text-[11px] text-[#667085] mt-0.5">
            Operational Region: Sector 4 Chennai & Coastal Command
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <select
            value={selectedIncident}
            onChange={(e) => setSelectedIncident(e.target.value)}
            className="px-2.5 py-1 bg-[#F7F8FA] border border-[#E4E7EC] rounded text-[#172033] font-semibold text-xs focus:outline-none"
          >
            {DEMO_INCIDENTS.map((i) => (
              <option key={i.id} value={i.id}>
                {i.id} - {i.title}
              </option>
            ))}
          </select>

          <button
            onClick={() => refetch()}
            className="px-3 py-1 bg-white border border-[#E4E7EC] hover:bg-slate-50 text-[#172033] font-semibold text-xs rounded transition-colors"
          >
            Refresh
          </button>

          <Link
            to="/prediction"
            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded transition-colors"
          >
            AI Decision Support
          </Link>
        </div>
      </div>

      {/* Compact Status Strip */}
      <div className="bg-white border border-[#E4E7EC] rounded-md p-3 grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs divide-x divide-slate-100 sm:divide-slate-200">
        <div className="px-2">
          <div className="text-[10px] uppercase font-bold text-[#667085]">Active Incidents</div>
          <div className="text-lg font-bold text-[#172033] mt-0.5">{activeIncidents}</div>
          <div className="text-[10px] text-red-700 font-medium">● 2 Red Level</div>
        </div>

        <div className="px-2 pl-3">
          <div className="text-[10px] uppercase font-bold text-[#667085]">Critical Cases</div>
          <div className="text-lg font-bold text-[#172033] mt-0.5">{criticalReports}</div>
          <div className="text-[10px] text-amber-700 font-medium">● Require Triage</div>
        </div>

        <div className="px-2 pl-3">
          <div className="text-[10px] uppercase font-bold text-[#667085]">People Affected</div>
          <div className="text-lg font-bold text-[#172033] mt-0.5">42,850</div>
          <div className="text-[10px] text-[#667085] font-medium">4 Sector Zones</div>
        </div>

        <div className="px-2 pl-3">
          <div className="text-[10px] uppercase font-bold text-[#667085]">Resources Deployed</div>
          <div className="text-lg font-bold text-[#172033] mt-0.5">{totalAllocated.toLocaleString()}</div>
          <div className="text-[10px] text-emerald-700 font-medium">● Transit Active</div>
        </div>

        <div className="px-2 pl-3">
          <div className="text-[10px] uppercase font-bold text-[#667085]">Available Shelters</div>
          <div className="text-lg font-bold text-[#172033] mt-0.5">{availableShelters.toLocaleString()}</div>
          <div className="text-[10px] text-[#667085] font-medium">Capacity Open</div>
        </div>
      </div>

      {/* Main Workspace Split Pane */}
      <div className="grid gap-4 lg:grid-cols-12">
        
        {/* LEFT ~55%: Active Incidents Operational Table (7 cols) */}
        <div className="lg:col-span-7 bg-white border border-[#E4E7EC] rounded-md overflow-hidden flex flex-col justify-between">
          <div className="p-3 border-b border-[#E4E7EC] bg-[#F7F8FA] flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#172033]">
              Active Incidents Registry ({reports.length > 0 ? reports.length : DEMO_INCIDENTS.length})
            </h2>
            <Link to="/sos" className="text-[11px] font-semibold text-blue-600 hover:underline">
              View All Distress Reports
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-[#E4E7EC] text-[10px] uppercase font-bold text-[#667085]">
                  <th className="py-2 px-3">Priority</th>
                  <th className="py-2 px-3">Ref ID</th>
                  <th className="py-2 px-3">Incident Title</th>
                  <th className="py-2 px-3">Location</th>
                  <th className="py-2 px-3 text-right">Affected</th>
                  <th className="py-2 px-3">Status</th>
                  <th className="py-2 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E4E7EC]">
                {DEMO_INCIDENTS.map((row) => (
                  <tr key={row.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-2 px-3 font-semibold">
                      <span className={`px-1.5 py-0.5 rounded text-[9px] uppercase font-bold ${
                        row.priority === "CRITICAL"
                          ? "bg-red-50 text-red-700 border border-red-200"
                          : row.priority === "HIGH"
                          ? "bg-amber-50 text-amber-700 border border-amber-200"
                          : "bg-blue-50 text-blue-700 border border-blue-200"
                      }`}>
                        {row.priority}
                      </span>
                    </td>
                    <td className="py-2 px-3 font-mono font-semibold text-[#172033]">{row.id}</td>
                    <td className="py-2 px-3 font-medium text-[#172033]">{row.title}</td>
                    <td className="py-2 px-3 text-[#667085]">{row.location}</td>
                    <td className="py-2 px-3 text-right font-mono font-medium">{row.affected.toLocaleString()}</td>
                    <td className="py-2 px-3">
                      <span className="text-[11px] text-emerald-700 font-medium">● {row.status}</span>
                    </td>
                    <td className="py-2 px-3 text-right space-x-1.5">
                      <button className="text-[10px] text-blue-600 font-semibold hover:underline">
                        View
                      </button>
                      <button className="text-[10px] text-blue-600 font-semibold hover:underline">
                        Dispatch
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* RIGHT ~45%: Operational Map & Critical Actions (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          
          {/* Operational Map Area */}
          <div className="bg-white border border-[#E4E7EC] rounded-md p-3 space-y-2">
            <div className="flex items-center justify-between border-b border-[#E4E7EC] pb-2 text-xs">
              <span className="font-bold text-[#172033]">Live Situation Map & Route Bypass</span>
              <span className="text-[10px] text-[#667085] font-mono">GRID: SECTOR 4</span>
            </div>

            <div className="bg-slate-900 rounded p-3 text-white text-xs font-mono space-y-2 min-h-[160px] flex flex-col justify-between">
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>OPERATIONAL MAP TELEMETRY</span>
                <span className="text-emerald-400 font-bold">● LIVE ROUTING</span>
              </div>

              <div className="space-y-1.5">
                <div className="p-1.5 bg-slate-800 rounded border border-slate-700 flex justify-between">
                  <span>Warehouse Sector 4</span>
                  <span className="text-emerald-400">DISPATCH READY</span>
                </div>

                <div className="p-1.5 bg-red-950/80 border border-red-800 rounded flex justify-between text-red-300">
                  <span>GST Underpass (Submerged 4ft)</span>
                  <span className="text-red-400 font-bold">● BLOCKED</span>
                </div>

                <div className="p-1.5 bg-slate-800 rounded border border-slate-700 flex justify-between text-blue-300">
                  <span>Bypass Arterial Expressway</span>
                  <span className="text-slate-300">ETA 31 MINS</span>
                </div>
              </div>

              <div className="text-[9px] text-slate-400 flex justify-between border-t border-slate-800 pt-1">
                <span>Active Fleet: 14 Vans</span>
                <span>Bypass Distance: +4.3 km</span>
              </div>
            </div>
          </div>

          {/* Critical Actions Panel */}
          <div className="bg-white border border-[#E4E7EC] rounded-md p-3 space-y-2 text-xs">
            <h3 className="font-bold text-[#172033] border-b border-[#E4E7EC] pb-1.5">
              Critical Immediate Actions
            </h3>
            <ul className="space-y-1.5 text-[11px] text-[#172033]">
              <li className="flex items-start space-x-1.5">
                <span className="text-red-600 font-bold">●</span>
                <span>Deploy 3 specialized medical teams to Tambaram Hospital ICU.</span>
              </li>
              <li className="flex items-start space-x-1.5">
                <span className="text-amber-600 font-bold">●</span>
                <span>Shelter capacity at Velachery Central below 15% threshold.</span>
              </li>
              <li className="flex items-start space-x-1.5">
                <span className="text-blue-600 font-bold">●</span>
                <span>Reroute heavy cargo convoy via Bypass Arterial Expressway.</span>
              </li>
            </ul>
          </div>

        </div>

      </div>

      {/* Lower Section: Resource Status & Capacity Tables */}
      <div className="grid gap-4 md:grid-cols-2">
        
        {/* Resource Allocation Table */}
        <div className="bg-white border border-[#E4E7EC] rounded-md p-3 space-y-2">
          <div className="flex items-center justify-between border-b border-[#E4E7EC] pb-2 text-xs">
            <span className="font-bold text-[#172033]">Resource Status & Allocation</span>
            <Link to="/resources" className="text-[11px] text-blue-600 font-semibold hover:underline">
              Manage Inventory
            </Link>
          </div>

          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#E4E7EC] text-[10px] uppercase font-bold text-[#667085]">
                <th className="py-1.5">Resource</th>
                <th className="py-1.5 text-right">Available</th>
                <th className="py-1.5 text-right">Allocated</th>
                <th className="py-1.5 text-right">Required</th>
                <th className="py-1.5 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E4E7EC]">
              <tr>
                <td className="py-1.5 font-semibold text-[#172033]">Emergency Water (2L)</td>
                <td className="py-1.5 text-right font-mono">12,500</td>
                <td className="py-1.5 text-right font-mono">9,200</td>
                <td className="py-1.5 text-right font-mono">15,000</td>
                <td className="py-1.5 text-center text-amber-700 font-medium">● Low Stock</td>
              </tr>
              <tr>
                <td className="py-1.5 font-semibold text-[#172033]">Type A Medical Kits</td>
                <td className="py-1.5 text-right font-mono">1,800</td>
                <td className="py-1.5 text-right font-mono">1,450</td>
                <td className="py-1.5 text-right font-mono">2,000</td>
                <td className="py-1.5 text-center text-emerald-700 font-medium">● Adequate</td>
              </tr>
              <tr>
                <td className="py-1.5 font-semibold text-[#172033]">High-Calorie Rations</td>
                <td className="py-1.5 text-right font-mono">8,400</td>
                <td className="py-1.5 text-right font-mono">6,000</td>
                <td className="py-1.5 text-right font-mono">8,000</td>
                <td className="py-1.5 text-center text-emerald-700 font-medium">● Adequate</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Shelter & Hospital Capacity */}
        <div className="bg-white border border-[#E4E7EC] rounded-md p-3 space-y-2">
          <div className="flex items-center justify-between border-b border-[#E4E7EC] pb-2 text-xs">
            <span className="font-bold text-[#172033]">Shelter & Hospital Bed Capacity</span>
            <Link to="/shelters" className="text-[11px] text-blue-600 font-semibold hover:underline">
              View All Facilities
            </Link>
          </div>

          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#E4E7EC] text-[10px] uppercase font-bold text-[#667085]">
                <th className="py-1.5">Facility Name</th>
                <th className="py-1.5">Type</th>
                <th className="py-1.5 text-right">Occupancy</th>
                <th className="py-1.5 text-right">Capacity</th>
                <th className="py-1.5 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E4E7EC]">
              {shelters.slice(0, 3).map((s) => (
                <tr key={s.id}>
                  <td className="py-1.5 font-semibold text-[#172033]">{s.shelter_name}</td>
                  <td className="py-1.5 text-[#667085]">Shelter</td>
                  <td className="py-1.5 text-right font-mono">{s.current_occupancy}</td>
                  <td className="py-1.5 text-right font-mono">{s.capacity}</td>
                  <td className="py-1.5 text-center text-emerald-700 font-medium">● Open</td>
                </tr>
              ))}
              {hospitals.slice(0, 1).map((h) => (
                <tr key={h.id}>
                  <td className="py-1.5 font-semibold text-[#172033]">{h.hospital_name}</td>
                  <td className="py-1.5 text-[#667085]">Hospital</td>
                  <td className="py-1.5 text-right font-mono">ICU: {h.icu_beds}</td>
                  <td className="py-1.5 text-right font-mono">Beds: {h.available_beds}</td>
                  <td className="py-1.5 text-center text-red-700 font-medium">● High Intake</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>

    </div>
  );
};
