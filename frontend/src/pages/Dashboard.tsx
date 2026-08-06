import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Flame,
  Home,
  HeartPulse,
  Users,
  Bell,
  RefreshCw,
  TrendingUp,
  Package,
  Map,
  Activity,
  MapPin,
  Clock,
  CheckCircle2,
  HelpCircle
} from "lucide-react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid
} from "recharts";
import { api, unwrapDashboardHospitals, unwrapEnvelope, unwrapList } from "../lib/api";

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: "#ef4444",
  HIGH: "#f97316",
  MEDIUM: "#eab308",
  LOW: "#3b82f6",
};

// ---------------------------------------------------------------------------
// Type definitions for API models
// ---------------------------------------------------------------------------
interface SummaryData {
  disasters: { total: number; active: number; resolved: number };
  emergency_reports: { total: number; verified: number; unverified: number };
  resources: { total: number; available: number; allocated: number };
  shelters: { total: number; total_capacity: number; current_occupancy: number; available_spots: number };
  hospitals: { total: number; total_available_beds: number; total_icu_beds: number };
  users: { total_active: number; volunteers: number };
  notifications: { unread: number };
}

interface StatisticsData {
  disasters: {
    by_status: Record<string, number>;
    by_severity: Record<string, number>;
  };
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
  latitude: number;
  longitude: number;
  address: string;
  description: string;
  is_verified: boolean;
  created_at: string;
}

interface NotificationData {
  id: string;
  title: string;
  message: string;
  priority: string;
  created_at: string;
}

export const Dashboard: React.FC = () => {
  // 1. Fetch KPI Summary
  const { 
    data: summary, 
    isLoading: isSummaryLoading, 
    isError: isSummaryError,
    refetch: refetchSummary 
  } = useQuery<SummaryData>({
    queryKey: ["dashboard-summary"],
    queryFn: async () => unwrapEnvelope<SummaryData>(await api.get("/dashboard/summary")),
  });

  // 2. Fetch Severity Statistics
  const { 
    data: stats, 
    isLoading: isStatsLoading, 
    isError: isStatsError,
    refetch: refetchStats
  } = useQuery<StatisticsData>({
    queryKey: ["dashboard-statistics"],
    queryFn: async () => unwrapEnvelope<StatisticsData>(await api.get("/dashboard/statistics")),
  });

  // 3. Fetch Shelters
  const { 
    data: sheltersRes, 
    isLoading: isSheltersLoading, 
    isError: isSheltersError,
    refetch: refetchShelters
  } = useQuery<ShelterData[]>({
    queryKey: ["shelters-list"],
    queryFn: async () => unwrapList<ShelterData>(await api.get("/shelters/")),
  });

  // 4. Fetch Ranked Hospitals
  const { 
    data: hospitalsRes, 
    isLoading: isHospitalsLoading, 
    isError: isHospitalsError,
    refetch: refetchHospitals
  } = useQuery<HospitalData[]>({
    queryKey: ["dashboard-hospitals"],
    queryFn: async () => unwrapDashboardHospitals<HospitalData>(await api.get("/dashboard/hospitals")),
  });

  // 5. Fetch Distress Reports
  const { 
    data: reportsRes, 
    isLoading: isReportsLoading, 
    isError: isReportsError,
    refetch: refetchReports
  } = useQuery<EmergencyReport[]>({
    queryKey: ["reports-list"],
    queryFn: async () => unwrapList<EmergencyReport>(await api.get("/reports/")),
  });

  // 6. Fetch Notifications
  const { 
    data: notificationsRes, 
    isLoading: isNotificationsLoading, 
    isError: isNotificationsError,
    refetch: refetchNotifications
  } = useQuery<NotificationData[]>({
    queryKey: ["notifications-list"],
    queryFn: async () => unwrapList<NotificationData>(await api.get("/notifications/")),
  });

  const refetchAll = () => {
    refetchSummary();
    refetchStats();
    refetchShelters();
    refetchHospitals();
    refetchReports();
    refetchNotifications();
  };

  const isLoading = 
    isSummaryLoading || 
    isStatsLoading || 
    isSheltersLoading || 
    isHospitalsLoading || 
    isReportsLoading || 
    isNotificationsLoading;

  const isError = 
    isSummaryError || 
    isStatsError || 
    isSheltersError || 
    isHospitalsError || 
    isReportsError || 
    isNotificationsError;

  // ---------------------------------------------------------------------------
  // Prepare data for charts
  // ---------------------------------------------------------------------------
  
  const disasterSeverityData = React.useMemo(() => {
    if (!stats?.disasters?.by_severity) return [];
    return Object.entries(stats.disasters.by_severity).map(([severity, count]) => ({
      name: severity.toUpperCase(),
      value: count,
      color: SEVERITY_COLORS[severity.toUpperCase()] || "#a855f7"
    }));
  }, [stats]);

  // Shelter Occupancy Bar Chart
  const shelterChartData = React.useMemo(() => {
    if (!Array.isArray(sheltersRes) || sheltersRes.length === 0) return [];
    return sheltersRes.map((shelter) => ({
      name: shelter.shelter_name.length > 20 ? shelter.shelter_name.slice(0, 18) + "..." : shelter.shelter_name,
      occupied: shelter.current_occupancy,
      capacity: shelter.capacity
    }));
  }, [sheltersRes]);

  // Hospital Capacity Chart
  const hospitalChartData = React.useMemo(() => {
    if (!Array.isArray(hospitalsRes) || hospitalsRes.length === 0) return [];
    return hospitalsRes.slice(0, 5).map((hosp) => ({
      name: hosp.hospital_name.length > 20 ? hosp.hospital_name.slice(0, 18) + "..." : hosp.hospital_name,
      General: hosp.available_beds,
      ICU: hosp.icu_beds
    }));
  }, [hospitalsRes]);

  // Sliced lists for tables and panels
  const recentReports = Array.isArray(reportsRes) ? reportsRes.slice(0, 5) : [];
  const recentNotifications = Array.isArray(notificationsRes)
    ? notificationsRes.slice(0, 5)
    : [];

  // Framer Motion Animation Variants
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    show: { y: 0, opacity: 1, transition: { type: "spring" as const, stiffness: 100 } }
  };

  return (
    <div className="space-y-8">
      {/* Top Banner with Refresh Status */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 bg-white border border-slate-200 rounded-2xl shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center">
            <Activity className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-800">Operational Summary</h2>
            <p className="text-xs text-slate-500">Real-time status updates from Madras Command Center.</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <span className="flex items-center space-x-1.5 px-3 py-1 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold rounded-full">
            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping" />
            <span>Systems Online</span>
          </span>
          <button 
            onClick={refetchAll} 
            disabled={isLoading}
            className="flex items-center space-x-2 px-4 py-2 border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-xl transition shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>Refresh EOC</span>
          </button>
        </div>
      </div>

      {/* Loading Skeletal State */}
      {isLoading && (
        <div className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-5">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-28 bg-slate-100 animate-pulse rounded-2xl border border-slate-200" />
            ))}
          </div>
          <div className="grid gap-6 lg:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-80 bg-slate-100 animate-pulse rounded-2xl border border-slate-200" />
            ))}
          </div>
        </div>
      )}

      {/* Error State Callout */}
      {isError && !isLoading && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-sm rounded-xl flex items-center space-x-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <div>
            <span className="font-semibold">Backend sync incomplete:</span> Some operational charts are showing fallback datasets due to network errors. Please verify that the FastAPI backend is running locally.
          </div>
        </div>
      )}

      {/* Main EOC content when available */}
      {!isLoading && (
        <motion.div 
          className="space-y-8"
          variants={containerVariants}
          initial="hidden"
          animate="show"
        >
          {/* 1. KPI grid */}
          <motion.div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-5" variants={itemVariants}>
            {[
              {
                title: "Active Disasters",
                value: summary?.disasters?.active ?? 0,
                desc: "Crisis response teams active",
                gradient: "from-rose-500/10 to-rose-600/5 border-l-rose-500",
                icon: AlertTriangle,
                iconColor: "text-rose-500 bg-rose-100"
              },
              {
                title: "Active SOS Reports",
                value: summary?.emergency_reports?.unverified ?? 0,
                desc: "Pending verification checks",
                gradient: "from-amber-500/10 to-amber-600/5 border-l-amber-500",
                icon: Flame,
                iconColor: "text-amber-500 bg-amber-100"
              },
              {
                title: "Shelter Spots Available",
                value: summary?.shelters?.available_spots ?? 0,
                desc: "Total open capacity",
                gradient: "from-emerald-500/10 to-emerald-600/5 border-l-emerald-500",
                icon: Home,
                iconColor: "text-emerald-500 bg-emerald-100"
              },
              {
                title: "Available Hosp Beds",
                value: summary?.hospitals?.total_available_beds ?? 0,
                desc: "Includes active ICU units",
                gradient: "from-cyan-500/10 to-cyan-600/5 border-l-cyan-500",
                icon: HeartPulse,
                iconColor: "text-cyan-500 bg-cyan-100"
              },
              {
                title: "Active Volunteers",
                value: summary?.users?.volunteers ?? 0,
                desc: "Responders currently online",
                gradient: "from-indigo-500/10 to-indigo-600/5 border-l-indigo-500",
                icon: Users,
                iconColor: "text-indigo-500 bg-indigo-100"
              }
            ].map((card, i) => {
              const Icon = card.icon;
              return (
                <motion.div 
                  key={i} 
                  whileHover={{ y: -4, scale: 1.02 }}
                  className={`p-5 bg-white border border-slate-200 border-l-4 ${card.gradient} rounded-2xl shadow-sm transition-all duration-200 flex flex-col justify-between`}
                >
                  <div className="flex items-start justify-between">
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{card.title}</span>
                    <div className={`p-2 rounded-xl ${card.iconColor}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="text-3xl font-extrabold text-slate-800">{card.value}</div>
                    <p className="text-[10px] text-slate-400 font-medium mt-1">{card.desc}</p>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>

          {/* 2. Quick Actions Panel */}
          <motion.div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm space-y-4" variants={itemVariants}>
            <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">Quick Action Operations</h3>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { title: "Run AI Prediction", path: "/prediction", color: "bg-indigo-600 hover:bg-indigo-700 shadow-indigo-600/10", icon: TrendingUp },
                { title: "Allocate Resources", path: "/resources", color: "bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/10", icon: Package },
                { title: "View Disaster Map", path: "/reports", color: "bg-cyan-600 hover:bg-cyan-700 shadow-cyan-600/10", icon: Map },
                { title: "Manage Shelters", path: "/shelters", color: "bg-purple-600 hover:bg-purple-700 shadow-purple-600/10", icon: Home }
              ].map((act, i) => {
                const Icon = act.icon;
                return (
                  <motion.div key={i} whileTap={{ scale: 0.98 }}>
                    <Link
                      to={act.path}
                      className={`flex items-center justify-between p-4 rounded-xl text-white font-medium text-sm transition shadow-md ${act.color}`}
                    >
                      <span className="tracking-tight">{act.title}</span>
                      <Icon className="w-5 h-5 text-white/90" />
                    </Link>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>

          {/* 3. Recharts Graphics Row */}
          <motion.div className="grid gap-6 lg:grid-cols-3" variants={itemVariants}>
            {/* Disaster Severity */}
            <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm flex flex-col justify-between min-h-[360px]">
              <div>
                <h3 className="text-sm font-semibold text-slate-800">Disaster Severity Overview</h3>
                <p className="text-xs text-slate-400 mt-1">Breakdown of current incidents by risk level.</p>
              </div>
              <div className="h-60 flex items-center justify-center mt-4">
                {disasterSeverityData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={disasterSeverityData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={3}
                        dataKey="value"
                      >
                        {disasterSeverityData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => [`${value} Disaster(s)`]} />
                      <Legend verticalAlign="bottom" height={36} iconType="circle" />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex flex-col items-center justify-center text-slate-400 text-xs">
                    <HelpCircle className="w-8 h-8 mb-2 text-slate-300" />
                    <span>No active disaster severity statistics.</span>
                  </div>
                )}
              </div>
            </div>

            {/* Shelter Occupancy */}
            <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm flex flex-col justify-between min-h-[360px] lg:col-span-1">
              <div>
                <h3 className="text-sm font-semibold text-slate-800">Shelter Occupancy</h3>
                <p className="text-xs text-slate-400 mt-1">Evacuee count compared to total safe capacity.</p>
              </div>
              <div className="h-60 mt-4">
                {shelterChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={shelterChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="occupied" fill="#4f46e5" name="Occupied" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="capacity" fill="#e2e8f0" name="Total Capacity" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex flex-col items-center justify-center text-slate-400 text-xs h-full">
                    <HelpCircle className="w-8 h-8 mb-2 text-slate-300" />
                    <span>No shelter occupancy logs available.</span>
                  </div>
                )}
              </div>
            </div>

            {/* Hospital Beds */}
            <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm flex flex-col justify-between min-h-[360px] lg:col-span-1">
              <div>
                <h3 className="text-sm font-semibold text-slate-800">Hospital Bed Capacity</h3>
                <p className="text-xs text-slate-400 mt-1">Ranked local hospitals by available general and ICU beds.</p>
              </div>
              <div className="h-60 mt-4">
                {hospitalChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={hospitalChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="General" stackId="a" fill="#0891b2" name="General Beds" />
                      <Bar dataKey="ICU" stackId="a" fill="#ec4899" name="ICU Beds" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex flex-col items-center justify-center text-slate-400 text-xs h-full">
                    <HelpCircle className="w-8 h-8 mb-2 text-slate-300" />
                    <span>No hospital capacity metrics synced.</span>
                  </div>
                )}
              </div>
            </div>
          </motion.div>

          {/* 4. Reports Table and System Notifications */}
          <motion.div className="grid gap-6 lg:grid-cols-3" variants={itemVariants}>
            {/* Recent Emergency Reports (2/3 width) */}
            <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm space-y-4 lg:col-span-2 overflow-hidden">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-800">Recent Emergency SOS Logs</h3>
                  <p className="text-xs text-slate-400 mt-1">Latest reports filed directly by citizens.</p>
                </div>
                <Link to="/reports" className="text-xs font-semibold text-indigo-600 hover:text-indigo-800">
                  View All
                </Link>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider">
                      <th className="pb-3 pr-2">Reporter</th>
                      <th className="pb-3 pr-2">Location</th>
                      <th className="pb-3 pr-2">Emergency</th>
                      <th className="pb-3 pr-2">Description</th>
                      <th className="pb-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50 text-slate-700">
                    {recentReports.length > 0 ? (
                      recentReports.map((report) => (
                        <tr key={report.id} className="hover:bg-slate-50/50 transition-colors duration-150">
                          <td className="py-3.5 pr-2 font-medium">
                            <div>{report.reporter_name}</div>
                            <div className="text-[10px] text-slate-400">{report.phone}</div>
                          </td>
                          <td className="py-3.5 pr-2">
                            <span className="flex items-center space-x-1">
                              <MapPin className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                              <span className="truncate max-w-[120px]">{report.address}</span>
                            </span>
                          </td>
                          <td className="py-3.5 pr-2">
                            <span className="px-2 py-0.5 rounded bg-indigo-50 border border-indigo-100 text-indigo-700 text-[10px] font-semibold uppercase">
                              {report.disaster_type}
                            </span>
                          </td>
                          <td className="py-3.5 pr-2">
                            <p className="truncate max-w-[180px] text-slate-500" title={report.description}>
                              {report.description}
                            </p>
                          </td>
                          <td className="py-3.5">
                            {report.is_verified ? (
                              <span className="flex items-center space-x-1 text-emerald-600 font-semibold">
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                <span>Verified</span>
                              </span>
                            ) : (
                              <span className="flex items-center space-x-1 text-amber-600 font-semibold">
                                <Clock className="w-3.5 h-3.5 animate-spin-slow" />
                                <span>Pending</span>
                              </span>
                            )}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="py-8 text-center text-slate-400 text-xs">
                          No distress incident logs registered in system database.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Recent Notifications (1/3 width) */}
            <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm space-y-4 lg:col-span-1 flex flex-col">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-800">EOC Bulletins & Alerts</h3>
                  <p className="text-xs text-slate-400 mt-1">Broadcast signals dispatched across portal.</p>
                </div>
                <Bell className="w-4 h-4 text-slate-400" />
              </div>

              <div className="flex-1 space-y-3.5 overflow-y-auto max-h-[260px] pr-1">
                {recentNotifications.length > 0 ? (
                  recentNotifications.map((notif) => {
                    const isCritical = notif.priority?.toUpperCase() === "CRITICAL";
                    const isHigh = notif.priority?.toUpperCase() === "HIGH";
                    const priorityColor = isCritical 
                      ? "bg-rose-50 border border-rose-200 text-rose-800" 
                      : isHigh 
                      ? "bg-amber-50 border border-amber-200 text-amber-800" 
                      : "bg-slate-50 border border-slate-200 text-slate-800";
                    
                    return (
                      <div key={notif.id} className={`p-3.5 rounded-xl transition duration-150 hover:shadow-sm ${priorityColor}`}>
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-semibold text-xs tracking-tight truncate">{notif.title}</span>
                          <span className="text-[9px] font-bold uppercase px-1.5 py-0.25 rounded-md border bg-white opacity-80">
                            {notif.priority}
                          </span>
                        </div>
                        <p className="text-[11px] mt-1.5 opacity-90 leading-relaxed font-medium">
                          {notif.message}
                        </p>
                      </div>
                    );
                  })
                ) : (
                  <div className="flex flex-col items-center justify-center text-slate-400 text-xs h-full py-8">
                    <Bell className="w-6 h-6 mb-2 text-slate-300" />
                    <span>No recent bulletin signals found.</span>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
};
