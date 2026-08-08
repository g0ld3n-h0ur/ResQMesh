import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Navigation,
  AlertTriangle,
  RefreshCw,
  Truck,
  ShieldAlert,
  AlertOctagon,
  Info
} from "lucide-react";

interface RouteInfo {
  id: string;
  origin: string;
  destination: string;
  vehicle_id: string;
  vehicle_type: string;
  status: "NORMAL" | "BLOCKED" | "REROUTED";
  original_distance_km: number;
  original_eta_mins: number;
  current_distance_km: number;
  current_eta_mins: number;
  blocked_road_name: string | null;
  reroute_reason: string | null;
  waypoints: Array<{ name: string; status: "OPEN" | "BLOCKED" | "PASSED" }>;
}

export const RoutingRerouting: React.FC = () => {
  const [routeState, setRouteState] = useState<RouteInfo>({
    id: "RT-8842",
    origin: "State Relief Warehouse - Sector 4",
    destination: "Tambaram General Hospital & Shelter Zone C",
    vehicle_id: "TN-01-EQ-9042 (Heavy Water Tanker & Medical Van)",
    vehicle_type: "Emergency Relief Truck",
    status: "NORMAL",
    original_distance_km: 18.5,
    original_eta_mins: 24,
    current_distance_km: 18.5,
    current_eta_mins: 24,
    blocked_road_name: null,
    reroute_reason: null,
    waypoints: [
      { name: "Warehouse Gate A", status: "PASSED" },
      { name: "GST Highway Flyover - Sector 2", status: "OPEN" },
      { name: "Grand Southern Trunk Underpass", status: "OPEN" },
      { name: "Tambaram Outer Ring Road", status: "OPEN" },
      { name: "Tambaram Hospital Gate", status: "OPEN" },
    ],
  });

  const [isSimulating, setIsSimulating] = useState(false);

  const handleSimulateRoadBlock = () => {
    setIsSimulating(true);
    setTimeout(() => {
      setRouteState(prev => ({
        ...prev,
        status: "REROUTED",
        blocked_road_name: "Grand Southern Trunk Underpass (Severe Flooding 4ft)",
        reroute_reason: "Automated sensor telemetry detected flash flooding water level > 1.2m across underpass. Dynamic routing engine recomputed bypass via Bypass Arterial Expressway.",
        current_distance_km: 22.8,
        current_eta_mins: 31,
        waypoints: [
          { name: "Warehouse Gate A", status: "PASSED" },
          { name: "GST Highway Flyover - Sector 2", status: "PASSED" },
          { name: "Grand Southern Trunk Underpass", status: "BLOCKED" },
          { name: "Bypass Arterial Expressway (Alternative)", status: "OPEN" },
          { name: "Tambaram Hospital Gate", status: "OPEN" },
        ],
      }));
      setIsSimulating(false);
    }, 1200);
  };

  const handleResetRoute = () => {
    setRouteState({
      id: "RT-8842",
      origin: "State Relief Warehouse - Sector 4",
      destination: "Tambaram General Hospital & Shelter Zone C",
      vehicle_id: "TN-01-EQ-9042 (Heavy Water Tanker & Medical Van)",
      vehicle_type: "Emergency Relief Truck",
      status: "NORMAL",
      original_distance_km: 18.5,
      original_eta_mins: 24,
      current_distance_km: 18.5,
      current_eta_mins: 24,
      blocked_road_name: null,
      reroute_reason: null,
      waypoints: [
        { name: "Warehouse Gate A", status: "PASSED" },
        { name: "GST Highway Flyover - Sector 2", status: "OPEN" },
        { name: "Grand Southern Trunk Underpass", status: "OPEN" },
        { name: "Tambaram Outer Ring Road", status: "OPEN" },
        { name: "Tambaram Hospital Gate", status: "OPEN" },
      ],
    });
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl text-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-600/30 shrink-0">
            <Navigation className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-extrabold tracking-tight">Dynamic Emergency Rerouting Simulator</h2>
              <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                DEMO / SIMULATION MODE
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Demonstrates automatic route recalculation when emergency road blockages or flash floods occur in transit.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleSimulateRoadBlock}
            disabled={routeState.status === "REROUTED" || isSimulating}
            className="px-4 py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-lg shadow-rose-600/20 flex items-center space-x-2 transition-all"
          >
            <AlertOctagon className="w-4 h-4" />
            <span>{isSimulating ? "Recalculating..." : "[Simulate Road Block]"}</span>
          </button>
          <button
            onClick={handleResetRoute}
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl border border-slate-700 flex items-center space-x-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset Route</span>
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left 2 Cols: Route Map Visualizer */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <Truck className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-800">Dispatch Vehicle Route Telemetry</h3>
                <p className="text-xs text-slate-400">Ref: {routeState.id} • {routeState.vehicle_id}</p>
              </div>
            </div>

            <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${
              routeState.status === "REROUTED"
                ? "bg-rose-50 text-rose-700 border-rose-200"
                : "bg-emerald-50 text-emerald-700 border-emerald-200"
            }`}>
              {routeState.status === "REROUTED" ? "DYNAMIC REROUTE ACTIVE" : "OPTIMAL ROUTE"}
            </span>
          </div>

          {/* Reroute Alert Message */}
          <AnimatePresence>
            {routeState.status === "REROUTED" && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 bg-rose-50 border border-rose-200 rounded-2xl text-rose-800 text-xs space-y-2"
              >
                <div className="flex items-center space-x-2 font-bold text-sm text-rose-900">
                  <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                  <span>ROAD BLOCKAGE DETECTED — ALTERNATIVE ROUTE CALCULATED</span>
                </div>
                <p className="text-xs text-rose-700 leading-relaxed">
                  <strong>Blocked Road:</strong> {routeState.blocked_road_name}
                </p>
                <p className="text-xs text-rose-700 leading-relaxed">
                  {routeState.reroute_reason}
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Visual Route Path Node Diagram */}
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 text-white space-y-6">
            <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
              <span>ORIGIN: {routeState.origin}</span>
              <span>DEST: {routeState.destination}</span>
            </div>

            {/* Waypoint Nodes Line */}
            <div className="relative py-4">
              <div className="absolute top-1/2 left-0 right-0 h-1 bg-slate-800 -translate-y-1/2" />
              {routeState.status === "REROUTED" && (
                <div className="absolute top-1/2 left-0 right-0 h-1 bg-rose-500/40 -translate-y-1/2 animate-pulse" />
              )}

              <div className="relative z-10 flex items-center justify-between">
                {routeState.waypoints.map((wp, idx) => (
                  <div key={idx} className="flex flex-col items-center group relative">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs shadow-md border-2 transition-all ${
                      wp.status === "BLOCKED"
                        ? "bg-rose-600 border-rose-400 text-white ring-4 ring-rose-600/30 scale-110"
                        : wp.status === "PASSED"
                        ? "bg-emerald-600 border-emerald-400 text-white"
                        : "bg-indigo-600 border-indigo-400 text-white"
                    }`}>
                      {wp.status === "BLOCKED" ? "✕" : idx + 1}
                    </div>
                    <span className="text-[10px] text-slate-300 font-medium mt-2 text-center max-w-[90px] leading-tight">
                      {wp.name}
                    </span>
                    <span className={`text-[9px] uppercase font-bold tracking-wider mt-0.5 px-1.5 py-0.2 rounded ${
                      wp.status === "BLOCKED"
                        ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                        : wp.status === "PASSED"
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-indigo-500/20 text-indigo-400"
                    }`}>
                      {wp.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Distance & ETA Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
              <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Distance</span>
                <span className="text-lg font-mono font-bold text-slate-100">
                  {routeState.current_distance_km} km
                </span>
                {routeState.status === "REROUTED" && (
                  <span className="text-[10px] text-rose-400 block mt-0.5">+4.3 km bypass</span>
                )}
              </div>

              <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Updated ETA</span>
                <span className="text-lg font-mono font-bold text-indigo-400">
                  {routeState.current_eta_mins} mins
                </span>
                {routeState.status === "REROUTED" && (
                  <span className="text-[10px] text-amber-400 block mt-0.5">+7 mins delay</span>
                )}
              </div>

              <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Traffic Status</span>
                <span className="text-xs font-semibold text-emerald-400 block mt-1">
                  {routeState.status === "REROUTED" ? "Heavy rerouted traffic" : "Optimal Flow"}
                </span>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Safety Index</span>
                <span className="text-xs font-semibold text-indigo-300 block mt-1">
                  {routeState.status === "REROUTED" ? "94.2% Safe Bypass" : "99.0% Safe"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right 1 Col: Route Specs & Telemetry */}
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-4">
            <h4 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-indigo-600" />
              <span>Route Dispatch Details</span>
            </h4>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Assigned Vehicle</span>
                <span className="font-semibold text-slate-800">{routeState.vehicle_id}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Cargo Manifest</span>
                <span className="font-semibold text-slate-800">500 Medical Kits, 2000L Drinking Water</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Primary Destination</span>
                <span className="font-semibold text-slate-800">{routeState.destination}</span>
              </div>
            </div>

            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-[11px] leading-relaxed flex items-start space-x-2">
              <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <span>
                Rerouting calculation is performed on the backend routing engine. In simulation mode, click <strong>[Simulate Road Block]</strong> above to test automatic obstacle detection.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
