import React, { useState } from "react";
import {
  BarChart3,
  Sliders
} from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";

const RESPONSE_SLA_DATA = [
  { metric: "Triage / AI Classify", target_mins: 2, actual_mins: 1.4, status: "MET" },
  { metric: "Team Assignment", target_mins: 15, actual_mins: 12.0, status: "MET" },
  { metric: "Warehouse Dispatch", target_mins: 30, actual_mins: 28.5, status: "MET" },
  { metric: "First Unit On-Site", target_mins: 45, actual_mins: 52.0, status: "BREACHED" },
  { metric: "Full Resolution", target_mins: 240, actual_mins: 210.0, status: "MET" },
];

export const SLAAnalyticsAAR: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"sla" | "aar" | "simulator">("sla");

  // Preparedness Simulator Form State
  const [simMagnitude, setSimMagnitude] = useState(7.5);
  const [simPopulation, setSimPopulation] = useState(50000);
  const [simFloodRainfall, setSimFloodRainfall] = useState(250);

  const estimatedWaterLiters = simPopulation * 3 * 7; // 3L/person/day for 7 days
  const estimatedFoodKg = simPopulation * 0.5 * 7; // 0.5kg/person/day for 7 days
  const estimatedShelterBeds = Math.round(simPopulation * 0.15); // 15% displacement
  const estimatedVolunteers = Math.round(simPopulation / 200);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl text-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-600/30 shrink-0">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-extrabold tracking-tight">SLA Analytics, AAR & Preparedness Simulator</h2>
              <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                DISASTER ANALYTICS ENGINE
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Data-backed response SLAs, post-disaster After-Action Review (AAR) reports, and scenario preparedness forecasting.
            </p>
          </div>
        </div>

        {/* Tab selector */}
        <div className="flex bg-slate-950 p-1.5 rounded-2xl border border-slate-800 space-x-1">
          <button
            onClick={() => setActiveTab("sla")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
              activeTab === "sla" ? "bg-indigo-600 text-white shadow-sm" : "text-slate-400 hover:text-white"
            }`}
          >
            SLA Response Analytics
          </button>
          <button
            onClick={() => setActiveTab("aar")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
              activeTab === "aar" ? "bg-indigo-600 text-white shadow-sm" : "text-slate-400 hover:text-white"
            }`}
          >
            After-Action Review (AAR)
          </button>
          <button
            onClick={() => setActiveTab("simulator")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
              activeTab === "simulator" ? "bg-purple-600 text-white shadow-sm" : "text-slate-400 hover:text-white"
            }`}
          >
            Preparedness Simulator
          </button>
        </div>
      </div>

      {activeTab === "sla" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
              <span className="text-xs text-slate-400 font-semibold block">Avg Triage Response</span>
              <span className="text-2xl font-black text-slate-800">1.4 mins</span>
              <span className="text-[10px] text-emerald-600 font-bold block mt-1">30% under SLA target</span>
            </div>

            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
              <span className="text-xs text-slate-400 font-semibold block">Dispatch Lead Time</span>
              <span className="text-2xl font-black text-indigo-600">28.5 mins</span>
              <span className="text-[10px] text-emerald-600 font-bold block mt-1">Within SLA target</span>
            </div>

            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
              <span className="text-xs text-slate-400 font-semibold block">SLA Compliance Rate</span>
              <span className="text-2xl font-black text-emerald-600">92.4%</span>
              <span className="text-[10px] text-slate-400 block mt-1">Across 420 active incidents</span>
            </div>

            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
              <span className="text-xs text-slate-400 font-semibold block">SLA Breaches</span>
              <span className="text-2xl font-black text-rose-600">1 Breach</span>
              <span className="text-[10px] text-rose-600 font-bold block mt-1">On-Site arrival delayed by road flood</span>
            </div>
          </div>

          {/* SLA Chart */}
          <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-800 border-b border-slate-100 pb-3">
              Response Milestone Benchmarks vs SLA Targets (Minutes)
            </h3>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={RESPONSE_SLA_DATA}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="metric" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: "11px" }} />
                  <Bar dataKey="target_mins" name="SLA Target (Mins)" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="actual_mins" name="Actual Performance (Mins)" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {activeTab === "aar" && (
        <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-600">
                OFFICIAL REPORT
              </span>
              <h3 className="text-lg font-bold text-slate-800">DATA-BACKED AFTER-ACTION REVIEW (AAR)</h3>
              <p className="text-xs text-slate-400">Incident: Severe Coastal Inundation Sector 4</p>
            </div>
            <span className="text-xs font-mono bg-slate-100 px-3 py-1 rounded-lg text-slate-600">
              STATUS: RESOLVED & AUDITED
            </span>
          </div>

          <div className="grid md:grid-cols-3 gap-4 text-xs">
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
              <h4 className="font-bold text-slate-800">1. Response Performance</h4>
              <p className="text-slate-600">Triage time: <strong>1.4 mins</strong> (Target 2 mins)</p>
              <p className="text-slate-600">Total units dispatched: <strong>1,450</strong></p>
              <p className="text-slate-600">Total resolved incidents: <strong>98.2%</strong></p>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
              <h4 className="font-bold text-slate-800">2. Bottlenecks Identified</h4>
              <p className="text-slate-600">Submerged arterial underpass caused <strong>7-minute transit delay</strong>.</p>
              <p className="text-slate-600">ICU Bed capacity reached <strong>98% occupancy</strong> at Peak Hour 4.</p>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
              <h4 className="font-bold text-slate-800">3. Actionable Recommendations</h4>
              <p className="text-slate-600">Pre-position high-clearance rescue vehicles in Sector 2.</p>
              <p className="text-slate-600">Establish secondary field hospital at Sector 4 Sports Complex.</p>
            </div>
          </div>
        </div>
      )}

      {activeTab === "simulator" && (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Simulator Form Inputs */}
          <div className="lg:col-span-1 bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-4">
            <div className="flex items-center space-x-2">
              <Sliders className="w-5 h-5 text-indigo-600" />
              <h3 className="text-base font-bold text-slate-800">Scenario Inputs</h3>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Impacted Population</label>
                <input
                  type="number"
                  value={simPopulation}
                  onChange={(e) => setSimPopulation(parseInt(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-medium"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Disaster Severity / Rainfall (mm)</label>
                <input
                  type="number"
                  value={simFloodRainfall}
                  onChange={(e) => setSimFloodRainfall(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-medium"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Earthquake Magnitude (Richter)</label>
                <input
                  type="number"
                  step="0.1"
                  value={simMagnitude}
                  onChange={(e) => setSimMagnitude(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-medium"
                />
              </div>
            </div>
          </div>

          {/* Simulator Output Estimation */}
          <div className="lg:col-span-2 bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-purple-100 text-purple-800 border border-purple-200">
                  SCENARIO ESTIMATION
                </span>
                <h3 className="text-base font-bold text-slate-800 mt-1">Resource Demand & Capacity Gap Forecast</h3>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl">
                <span className="text-slate-400 block text-[10px] uppercase font-bold">7-Day Water Demand</span>
                <span className="text-xl font-bold font-mono text-indigo-600">{estimatedWaterLiters.toLocaleString()} Liters</span>
              </div>

              <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl">
                <span className="text-slate-400 block text-[10px] uppercase font-bold">7-Day Food Stock Needed</span>
                <span className="text-xl font-bold font-mono text-indigo-600">{estimatedFoodKg.toLocaleString()} kg</span>
              </div>

              <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl">
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Shelter Bed Requirement</span>
                <span className="text-xl font-bold font-mono text-purple-600">{estimatedShelterBeds.toLocaleString()} Beds</span>
              </div>

              <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl">
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Volunteers Required</span>
                <span className="text-xl font-bold font-mono text-emerald-600">{estimatedVolunteers.toLocaleString()} Volunteers</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
