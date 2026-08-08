import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  Home,
  Users,
  Bell,
  RefreshCw,
  Package,
  MapPin,
  Clock,
  Navigation,
  ShieldAlert,
  ArrowUpRight
} from "lucide-react";
import { api, unwrapDashboardHospitals, unwrapEnvelope, unwrapList } from "../lib/api";

interface SummaryData {
  disasters: { total: number; active: number; resolved: number };
  emergency_reports: { total: number; verified: number; unverified: number };
  resources: { total: number; available: number; allocated: number };
  shelters: { total: number; total_capacity: number; current_occupancy: number; available_spots: number };
  hospitals: { total: number; total_available_beds: number; total_icu_beds: number };
  users: { total_active: number; volunteers: number };
  notifications: { unread: number };
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
  latitude: number | null;
  longitude: number | null;
  address: string;
  description: string;
  is_verified: boolean;
  created_at: string;
}

const LIVE_REFRESH_MS = 20_000;

export const Dashboard: React.FC = () => {
  const { data: summary, isLoading: isSummaryLoading, refetch } = useQuery<SummaryData>({
    queryKey: ["dashboard-summary"],
    queryFn: async () => unwrapEnvelope<SummaryData>(await api.get("/dashboard/summary")),
    refetchInterval: LIVE_REFRESH_MS,
  });

  const { data: shelters = [] } = useQuery<ShelterData[]>({
    queryKey: ["dashboard-shelters"],
    queryFn: async () => unwrapList<ShelterData>(await api.get("/dashboard/shelters")),
    refetchInterval: LIVE_REFRESH_MS,
  });

  const { data: hospitals = [] } = useQuery<HospitalData[]>({
    queryKey: ["dashboard-hospitals"],
    queryFn: async () => unwrapDashboardHospitals<HospitalData>(await api.get("/dashboard/hospitals")),
    refetchInterval: LIVE_REFRESH_MS,
  });

  const { data: reports = [] } = useQuery<EmergencyReport[]>({
    queryKey: ["emergency-reports"],
    queryFn: async () => unwrapList<EmergencyReport>(await api.get("/reports/")),
    refetchInterval: LIVE_REFRESH_MS,
  });

  const activeIncidentsCount = summary?.disasters?.active ?? 4;
  const unverifiedReportsCount = summary?.emergency_reports?.unverified ?? 12;
  const allocatedResources = summary?.resources?.allocated ?? 18500;
  const availableShelterSpots = summary?.shelters?.available_spots ?? 1240;

  return (
    <div className="space-y-5 font-sans">
      
      {/* Top Section: Operational Header Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-3 h-3 rounded-full bg-rose-600 animate-ping shrink-0" />
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-extrabold text-slate-900 tracking-tight">
                State Operational Status: Severe Coastal Flood Response
              </h2>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-200">
                LEVEL 2 EMERGENCY
              </span>
            </div>
            <div className="text-xs text-slate-500 flex items-center space-x-3 mt-0.5">
              <span className="flex items-center space-x-1">
                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                <span>Sector 4 - Chennai & Coastal Districts</span>
              </span>
              <span>•</span>
              <span className="flex items-center space-x-1">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>Last Synced: {new Date().toLocaleTimeString()}</span>
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => refetch()}
            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg border border-slate-200 flex items-center space-x-1.5 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Sync Telemetry</span>
          </button>
          <Link
            to="/prediction"
            className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg shadow-2xs flex items-center space-x-1 transition-colors"
          >
            <span>AI Decision Support</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* KPI Row: 5 Compact Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-[11px] font-bold uppercase tracking-wider">
            <span>Active Disasters</span>
            <AlertTriangle className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">
            {isSummaryLoading ? "..." : activeIncidentsCount}
          </div>
          <div className="text-[10px] text-rose-600 font-medium">2 Critical Red Alerts</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-3.5 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-[11px] font-bold uppercase tracking-wider">
            <span>People Affected</span>
            <Users className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">42,850</div>
          <div className="text-[10px] text-slate-500 font-medium">Estimated across 4 zones</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-[11px] font-bold uppercase tracking-wider">
            <span>Triage Requests</span>
            <Bell className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-black text-indigo-700">
            {isSummaryLoading ? "..." : unverifiedReportsCount}
          </div>
          <div className="text-[10px] text-indigo-600 font-medium">Pending Verification</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-[11px] font-bold uppercase tracking-wider">
            <span>Resources Dispatched</span>
            <Package className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">
            {isSummaryLoading ? "..." : allocatedResources.toLocaleString()}
          </div>
          <div className="text-[10px] text-emerald-600 font-medium">Units in Transit</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-[11px] font-bold uppercase tracking-wider">
            <span>Shelter Capacity</span>
            <Home className="w-4 h-4 text-purple-600" />
          </div>
          <div className="text-2xl font-black text-purple-700">
            {isSummaryLoading ? "..." : availableShelterSpots.toLocaleString()}
          </div>
          <div className="text-[10px] text-slate-500 font-medium">Available Spots</div>
        </div>
      </div>

      {/* Main 3-Column Area */}
      <div className="grid gap-5 lg:grid-cols-12">
        
        {/* LEFT: Active Incidents Table (4 cols) */}
        <div className="lg:col-span-4 bg-white border border-slate-200 rounded-xl shadow-2xs overflow-hidden flex flex-col justify-between">
          <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
              Active Incidents Queue ({reports.length})
            </h3>
            <Link to="/reports" className="text-[11px] font-bold text-indigo-600 hover:text-indigo-800">
              View All
            </Link>
          </div>

          <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
            {reports.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400 font-medium">
                No unverified distress reports pending.
              </div>
            ) : (
              reports.slice(0, 5).map((rep) => (
                <div key={rep.id} className="p-3 hover:bg-slate-50 transition-colors text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 truncate max-w-[180px]">{rep.disaster_type}</span>
                    <span className={`px-2 py-0.5 rounded text-[9px] uppercase font-bold border ${
                      rep.is_verified
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : "bg-amber-50 text-amber-700 border-amber-200"
                    }`}>
                      {rep.is_verified ? "VERIFIED" : "UNVERIFIED"}
                    </span>
                  </div>
                  <p className="text-slate-600 text-[11px] line-clamp-1">{rep.description}</p>
                  <div className="text-[10px] text-slate-400 flex items-center justify-between pt-0.5">
                    <span>Loc: {rep.address}</span>
                    <span>{new Date(rep.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* CENTER: Operational Area Telemetry Map (5 cols) */}
        <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl shadow-2xs p-4 flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <Navigation className="w-4 h-4 text-indigo-600" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                Operational Zone Map & Route Telemetry
              </h3>
            </div>
            <Link to="/routing" className="text-[11px] font-bold text-indigo-600 hover:text-indigo-800">
              Interactive Map
            </Link>
          </div>

          <div className="bg-slate-900 rounded-xl p-4 text-white space-y-4 relative overflow-hidden min-h-[260px] flex flex-col justify-between">
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
              <span>ZONE: SECTOR 4 CHENNAI SOUTH</span>
              <span className="text-emerald-400 font-bold">ROUTING ENGINE ACTIVE</span>
            </div>

            {/* Sim Map Telemetry Nodes */}
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs bg-slate-800/80 p-2.5 rounded-lg border border-slate-700">
                <div className="flex items-center space-x-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  <span className="font-semibold text-slate-200">Relief Warehouse Sector 4</span>
                </div>
                <span className="font-mono text-slate-400 text-[11px]">DISPATCH READY</span>
              </div>

              <div className="flex items-center justify-between text-xs bg-rose-950/60 p-2.5 rounded-lg border border-rose-800/80 text-rose-200">
                <div className="flex items-center space-x-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
                  <span className="font-semibold">GST Underpass (Submerged 4ft)</span>
                </div>
                <span className="font-mono text-rose-300 text-[10px] font-bold">BLOCKED</span>
              </div>

              <div className="flex items-center justify-between text-xs bg-slate-800/80 p-2.5 rounded-lg border border-slate-700">
                <div className="flex items-center space-x-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
                  <span className="font-semibold text-slate-200">Bypass Arterial Expressway</span>
                </div>
                <span className="font-mono text-indigo-300 text-[11px]">REROUTE ETA: 31 MINS</span>
              </div>
            </div>

            <div className="text-[10px] text-slate-400 font-mono flex justify-between border-t border-slate-800 pt-2">
              <span>Active Vehicles: 14 Truck Fleet</span>
              <span>Reroute Bypass: +4.3 km</span>
            </div>
          </div>
        </div>

        {/* RIGHT: Critical Alerts & Action Items (3 cols) */}
        <div className="lg:col-span-3 bg-white border border-slate-200 rounded-xl shadow-2xs p-4 flex flex-col justify-between space-y-3">
          <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
            <ShieldAlert className="w-4 h-4 text-rose-600" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
              Critical Alerts & Action Items
            </h3>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-lg text-rose-900 space-y-1">
              <span className="font-bold text-[11px] block">ICU Bed Shortage - Apollo Unit</span>
              <p className="text-[11px] text-rose-700 leading-tight">Only 2 ICU beds remaining. Re-route critical trauma cases to General Hospital.</p>
            </div>

            <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 space-y-1">
              <span className="font-bold text-[11px] block">Water Stock Depleting</span>
              <p className="text-[11px] text-amber-700 leading-tight">Velachery Shelter inventory at 15%. Dispatch batch RES-WATER-99.</p>
            </div>

            <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-700 space-y-1">
              <span className="font-bold text-[11px] block">Volunteer Squad Alpha</span>
              <p className="text-[11px] text-slate-600 leading-tight">15 volunteers assigned to medical triage at Sector 2.</p>
            </div>
          </div>
        </div>

      </div>

      {/* Lower Section: Compact Operational Panels */}
      <div className="grid gap-5 md:grid-cols-2">
        {/* Shelter Capacity Summary */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-2xs p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
              Emergency Shelter Occupancy
            </h3>
            <Link to="/shelters" className="text-[11px] font-bold text-indigo-600 hover:text-indigo-800">
              Manage Shelters
            </Link>
          </div>

          <div className="space-y-2">
            {shelters.slice(0, 3).map((shelter) => {
              const occPct = Math.round((shelter.current_occupancy / shelter.capacity) * 100);
              return (
                <div key={shelter.id} className="text-xs space-y-1">
                  <div className="flex justify-between font-semibold text-slate-800">
                    <span>{shelter.shelter_name} ({shelter.district})</span>
                    <span>{shelter.current_occupancy} / {shelter.capacity} ({occPct}%)</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-1.5 rounded-full ${occPct > 85 ? "bg-rose-600" : "bg-indigo-600"}`}
                      style={{ width: `${occPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Hospital Fleet Capacity */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-2xs p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
              Hospital ICU & Bed Capacity
            </h3>
            <Link to="/hospitals" className="text-[11px] font-bold text-indigo-600 hover:text-indigo-800">
              View Hospitals
            </Link>
          </div>

          <div className="space-y-2 text-xs">
            {hospitals.slice(0, 3).map((hosp) => (
              <div key={hosp.id} className="flex items-center justify-between p-2 bg-slate-50 border border-slate-200 rounded-lg">
                <span className="font-semibold text-slate-800">{hosp.hospital_name}</span>
                <div className="flex items-center space-x-3 text-[11px]">
                  <span className="font-bold text-slate-700">Available: {hosp.available_beds} Beds</span>
                  <span className="font-bold text-rose-600">ICU: {hosp.icu_beds}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

    </div>
  );
};
