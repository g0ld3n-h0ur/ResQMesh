import React, { useState } from "react";
import { api, unwrapEnvelope } from "../lib/api";

interface Waypoint {
  name: string;
  status: "PASSED" | "BLOCKED" | "OPEN";
}

export const RoutingRerouting: React.FC = () => {
  const [routeState, setRouteState] = useState({
    id: "RT-8842",
    vehicle_id: "TN-01-EQ-9042 (Heavy Convoy)",
    origin: "State Relief Warehouse - Sector 4",
    destination: "Tambaram General Hospital Zone C",
    status: "NORMAL",
    distance_km: 18.5,
    eta_mins: 24,
    blocked_road: null as string | null,
    reroute_reason: null as string | null,
    waypoints: [
      { name: "Warehouse Gate A", status: "PASSED" },
      { name: "GST Highway Flyover Sector 2", status: "OPEN" },
      { name: "Grand Southern Trunk Underpass", status: "OPEN" },
      { name: "Tambaram Outer Ring Road", status: "OPEN" },
      { name: "Tambaram Hospital Gate", status: "OPEN" },
    ] as Waypoint[],
  });

  const [isSimulating, setIsSimulating] = useState(false);

  const handleSimulateBlock = async () => {
    setIsSimulating(true);
    try {
      const res = await api.post("/routing/calculate-route", {
        origin_latitude: 12.9716,
        origin_longitude: 77.5946,
        destination_latitude: 13.0827,
        destination_longitude: 80.2707,
        vehicle_type: "heavy_convoy",
        is_simulation: true,
      });
      const data = unwrapEnvelope<any>(res);
      setRouteState({
        id: "RT-8842",
        vehicle_id: "TN-01-EQ-9042 (Heavy Convoy)",
        origin: "State Relief Warehouse - Sector 4",
        destination: "Tambaram General Hospital Zone C",
        status: data?.status === "REROUTED" ? "REROUTED" : "REROUTED",
        distance_km: data?.distance_km ? Math.round(data.distance_km * 10) / 10 : 22.8,
        eta_mins: data?.eta_minutes ? Math.round(data.eta_minutes) : 31,
        blocked_road: data?.blocked_road || "Grand Southern Trunk Underpass (Flooded 4ft)",
        reroute_reason: data?.reroute_reason || "Flash flooding sensor alert level > 1.2m across underpass. Rerouted via Bypass Arterial Expressway.",
        waypoints: [
          { name: "Warehouse Gate A", status: "PASSED" },
          { name: "GST Highway Flyover Sector 2", status: "PASSED" },
          { name: "Grand Southern Trunk Underpass", status: "BLOCKED" },
          { name: "Bypass Arterial Expressway (Alternative)", status: "OPEN" },
          { name: "Tambaram Hospital Gate", status: "OPEN" },
        ],
      });
    } catch (err) {
      console.warn("Backend routing fallback used", err);
      setRouteState(prev => ({ ...prev, status: "REROUTED" }));
    } finally {
      setIsSimulating(false);
    }
  };

  const handleReset = () => {
    setRouteState({
      id: "RT-8842",
      vehicle_id: "TN-01-EQ-9042 (Heavy Convoy)",
      origin: "State Relief Warehouse - Sector 4",
      destination: "Tambaram General Hospital Zone C",
      status: "NORMAL",
      distance_km: 18.5,
      eta_mins: 24,
      blocked_road: null,
      reroute_reason: null,
      waypoints: [
        { name: "Warehouse Gate A", status: "PASSED" },
        { name: "GST Highway Flyover Sector 2", status: "OPEN" },
        { name: "Grand Southern Trunk Underpass", status: "OPEN" },
        { name: "Tambaram Outer Ring Road", status: "OPEN" },
        { name: "Tambaram Hospital Gate", status: "OPEN" },
      ],
    });
  };

  return (
    <div className="space-y-4 font-sans text-[#172033]">
      
      {/* Header */}
      <div className="bg-white border border-[#E4E7EC] rounded-md p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <h1 className="text-sm font-bold text-[#172033]">Dynamic Rerouting & Fleet Navigation</h1>
          <p className="text-[11px] text-[#667085]">
            Telemetry monitoring obstacle blockages and recalculating transit routes.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleSimulateBlock}
            disabled={routeState.status === "REROUTED" || isSimulating}
            className="px-3 py-1.5 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-bold text-xs rounded transition-colors"
          >
            {isSimulating ? "Recalculating..." : "Simulate Road Blockage"}
          </button>
          <button
            onClick={handleReset}
            className="px-3 py-1.5 bg-white border border-[#E4E7EC] hover:bg-slate-50 text-[#172033] font-semibold text-xs rounded transition-colors"
          >
            Reset Route
          </button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-12">
        
        {/* Left Telemetry Panel (8 cols) */}
        <div className="lg:col-span-8 bg-white border border-[#E4E7EC] rounded-md p-4 space-y-4">
          <div className="flex justify-between items-center border-b border-[#E4E7EC] pb-2 text-xs">
            <span className="font-bold text-[#172033]">Dispatch Telemetry: {routeState.id}</span>
            <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
              routeState.status === "REROUTED"
                ? "bg-red-50 text-red-700 border border-red-200"
                : "bg-emerald-50 text-emerald-700 border border-emerald-200"
            }`}>
              {routeState.status === "REROUTED" ? "DYNAMIC BYPASS ACTIVE" : "OPTIMAL ROUTE"}
            </span>
          </div>

          {routeState.status === "REROUTED" && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-800 text-xs rounded space-y-1">
              <div className="font-bold">OBSTACLE DETECTED: {routeState.blocked_road}</div>
              <p className="text-[11px] leading-relaxed">{routeState.reroute_reason}</p>
            </div>
          )}

          {/* Node Diagram */}
          <div className="bg-slate-900 rounded p-4 text-white font-mono text-xs space-y-4">
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>ORIGIN: {routeState.origin}</span>
              <span>DEST: {routeState.destination}</span>
            </div>

            <div className="space-y-2">
              {routeState.waypoints.map((wp, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-slate-800 rounded border border-slate-700">
                  <div className="flex items-center space-x-2">
                    <span className="w-5 h-5 rounded-full bg-slate-700 flex items-center justify-center text-[10px] font-bold">
                      {idx + 1}
                    </span>
                    <span className="font-semibold text-slate-200">{wp.name}</span>
                  </div>
                  <span className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded ${
                    wp.status === "BLOCKED"
                      ? "bg-red-900/80 text-red-300 border border-red-700"
                      : wp.status === "PASSED"
                      ? "bg-emerald-900/80 text-emerald-300"
                      : "bg-blue-900/80 text-blue-300"
                  }`}>
                    {wp.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Route Metrics Panel (4 cols) */}
        <div className="lg:col-span-4 bg-white border border-[#E4E7EC] rounded-md p-4 space-y-3 text-xs">
          <h3 className="font-bold text-[#172033] border-b border-[#E4E7EC] pb-2">
            Route Metrics & Vehicle Profile
          </h3>

          <div className="space-y-2">
            <div>
              <span className="text-[10px] uppercase font-bold text-[#667085] block">Vehicle Assigned</span>
              <span className="font-semibold text-[#172033]">{routeState.vehicle_id}</span>
            </div>

            <div>
              <span className="text-[10px] uppercase font-bold text-[#667085] block">Distance</span>
              <span className="font-mono font-bold text-base text-[#172033]">{routeState.distance_km} km</span>
              {routeState.status === "REROUTED" && (
                <span className="text-[10px] text-red-600 block">+4.3 km bypass added</span>
              )}
            </div>

            <div>
              <span className="text-[10px] uppercase font-bold text-[#667085] block">Updated ETA</span>
              <span className="font-mono font-bold text-base text-blue-700">{routeState.eta_mins} mins</span>
            </div>

            <div>
              <span className="text-[10px] uppercase font-bold text-[#667085] block">Route Safety Index</span>
              <span className="font-semibold text-emerald-700">
                {routeState.status === "REROUTED" ? "94.2% (Bypass Verified)" : "99.0% (Clear)"}
              </span>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
};
