import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Gauge,
  AlertTriangle,
  MapPin,
  FileText,
  Package,
  Info,
  Navigation,
  Home,
  HeartPulse,
} from "lucide-react";
import { api, unwrapList } from "../lib/api";

interface NeedScoreBreakdown {
  severity_component: number;
  report_pressure_component: number;
  resource_shortfall_component: number;
  status_urgency_component: number;
}

interface NeedScore {
  disaster_id: string;
  title: string;
  disaster_type: string;
  severity: string;
  status: string;
  district: string | null;
  state: string | null;
  report_count: number;
  resources_assigned: number;
  need_score: number;
  need_level: string;
  rank: number;
  breakdown: NeedScoreBreakdown;
}

interface DistributionPriority {
  disaster_id: string;
  title: string;
  disaster_type: string;
  district: string | null;
  state: string | null;
  need_score: number;
  nearest_shelter_name: string | null;
  nearest_shelter_distance_km: number | null;
  nearest_hospital_name: string | null;
  nearest_hospital_distance_km: number | null;
  accessibility_score: number;
  accessibility_data_available: boolean;
  distribution_priority_score: number;
  rank: number;
}

const LEVEL_STYLES: Record<string, { badge: string; bar: string }> = {
  critical: { badge: "bg-rose-50 border-rose-200 text-rose-800", bar: "bg-rose-500" },
  high: { badge: "bg-amber-50 border-amber-200 text-amber-800", bar: "bg-amber-500" },
  medium: { badge: "bg-yellow-50 border-yellow-200 text-yellow-800", bar: "bg-yellow-400" },
  low: { badge: "bg-emerald-50 border-emerald-200 text-emerald-800", bar: "bg-emerald-500" },
};

const COMPONENT_LABELS: { key: keyof NeedScoreBreakdown; label: string; color: string }[] = [
  { key: "severity_component", label: "Assessed Severity", color: "bg-indigo-500" },
  { key: "report_pressure_component", label: "Citizen Report Volume", color: "bg-cyan-500" },
  { key: "resource_shortfall_component", label: "Resource Shortfall", color: "bg-rose-500" },
  { key: "status_urgency_component", label: "Lifecycle Urgency", color: "bg-purple-500" },
];

const TABS = [
  { key: "need", label: "Severity of Need" },
  { key: "distribution", label: "Urgency + Accessibility" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

const NeedScoreView: React.FC = () => {
  const { data: scores = [], isLoading, isError } = useQuery<NeedScore[]>({
    queryKey: ["disaster-need-scores"],
    queryFn: async () => unwrapList<NeedScore>(await api.get("/disasters/need-scores")),
    refetchInterval: 20_000,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-start space-x-2 p-3.5 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-700 text-xs">
        <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <span>
          The score is not the same as the manually-set severity level above it — it updates as
          reports come in and resources are consumed, so it can surface an under-resourced "high"
          disaster above a well-resourced "critical" one.
        </span>
      </div>

      {isLoading && (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-40 bg-slate-100 animate-pulse rounded-2xl border border-slate-200" />
          ))}
        </div>
      )}

      {isError && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-rose-600" />
          <span>Error computing need scores. Please confirm the backend is running.</span>
        </div>
      )}

      {!isLoading && !isError && (
        <div className="space-y-4">
          {scores.length > 0 ? (
            scores.map((item, i) => {
              const levelStyle = LEVEL_STYLES[item.need_level] ?? LEVEL_STYLES.low;
              return (
                <motion.div
                  key={item.disaster_id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                  className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start space-x-3">
                      <div className="w-9 h-9 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold text-sm flex-shrink-0">
                        #{item.rank}
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-slate-800">{item.title}</h3>
                        <div className="flex items-center flex-wrap gap-x-3 gap-y-1 mt-1 text-[10px] text-slate-500 font-semibold">
                          <span className="uppercase tracking-wider">{item.disaster_type}</span>
                          {(item.district || item.state) && (
                            <span className="flex items-center space-x-1">
                              <MapPin className="w-3 h-3" />
                              <span>{[item.district, item.state].filter(Boolean).join(", ")}</span>
                            </span>
                          )}
                          <span className="flex items-center space-x-1">
                            <FileText className="w-3 h-3" />
                            <span>{item.report_count} report(s)</span>
                          </span>
                          <span className="flex items-center space-x-1">
                            <Package className="w-3 h-3" />
                            <span>{item.resources_assigned} resource(s) assigned</span>
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col items-end space-y-1.5 flex-shrink-0">
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${levelStyle.badge}`}>
                        {item.need_level} need
                      </span>
                      <div className="flex items-center space-x-1.5">
                        <Gauge className="w-4 h-4 text-slate-400" />
                        <span className="text-xl font-black text-slate-800">{item.need_score.toFixed(1)}</span>
                        <span className="text-[10px] text-slate-400 font-semibold">/ 100</span>
                      </div>
                    </div>
                  </div>

                  {/* Breakdown bar */}
                  <div className="space-y-1.5">
                    <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden flex">
                      {COMPONENT_LABELS.map(({ key, color }) => (
                        <div
                          key={key}
                          className={color}
                          style={{ width: `${item.breakdown[key]}%` }}
                          title={`${key}: ${item.breakdown[key]}`}
                        />
                      ))}
                    </div>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-[9px] text-slate-500 font-semibold">
                      {COMPONENT_LABELS.map(({ key, label, color }) => (
                        <span key={key} className="flex items-center space-x-1">
                          <span className={`w-2 h-2 rounded-full ${color}`} />
                          <span>{label}: {item.breakdown[key].toFixed(1)}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                </motion.div>
              );
            })
          ) : (
            <div className="bg-white border border-slate-200 border-dashed rounded-2xl p-12 text-center text-slate-400 text-xs">
              <Gauge className="w-12 h-12 text-slate-300 mx-auto mb-3 animate-pulse" />
              <span>No active disasters to rank.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const DistributionPriorityView: React.FC = () => {
  const { data: items = [], isLoading, isError } = useQuery<DistributionPriority[]>({
    queryKey: ["disaster-distribution-priority"],
    queryFn: async () => unwrapList<DistributionPriority>(await api.get("/disasters/distribution-priority")),
    refetchInterval: 20_000,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-start space-x-2 p-3.5 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-700 text-xs">
        <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <span>
          Combines need score (60%) with accessibility (40%) — how close the disaster is to the
          nearest registered shelter and hospital. Two equally urgent disasters split by which one
          responders can actually reach fastest right now.
        </span>
      </div>

      {isLoading && (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-36 bg-slate-100 animate-pulse rounded-2xl border border-slate-200" />
          ))}
        </div>
      )}

      {isError && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-rose-600" />
          <span>Error computing distribution priority. Please confirm the backend is running.</span>
        </div>
      )}

      {!isLoading && !isError && (
        <div className="space-y-4">
          {items.length > 0 ? (
            items.map((item, i) => (
              <motion.div
                key={item.disaster_id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3.5"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start space-x-3">
                    <div className="w-9 h-9 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold text-sm flex-shrink-0">
                      #{item.rank}
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-800">{item.title}</h3>
                      <div className="flex items-center flex-wrap gap-x-3 gap-y-1 mt-1 text-[10px] text-slate-500 font-semibold">
                        <span className="uppercase tracking-wider">{item.disaster_type}</span>
                        {(item.district || item.state) && (
                          <span className="flex items-center space-x-1">
                            <MapPin className="w-3 h-3" />
                            <span>{[item.district, item.state].filter(Boolean).join(", ")}</span>
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1.5 flex-shrink-0">
                    <Navigation className="w-4 h-4 text-slate-400" />
                    <span className="text-xl font-black text-slate-800">{item.distribution_priority_score.toFixed(1)}</span>
                    <span className="text-[10px] text-slate-400 font-semibold">/ 100</span>
                  </div>
                </div>

                <div className="grid sm:grid-cols-3 gap-2.5 text-[10px] font-semibold">
                  <div className="bg-slate-50 border border-slate-100 rounded-xl p-2.5">
                    <span className="text-slate-400 uppercase tracking-wider block mb-0.5">Need score</span>
                    <span className="text-slate-800 text-sm font-black">{item.need_score.toFixed(1)}</span>
                  </div>
                  <div className="bg-slate-50 border border-slate-100 rounded-xl p-2.5 flex items-center justify-between">
                    <div>
                      <span className="text-slate-400 uppercase tracking-wider block mb-0.5 flex items-center space-x-1">
                        <Home className="w-3 h-3" /> <span>Nearest shelter</span>
                      </span>
                      <span className="text-slate-700">
                        {item.nearest_shelter_name ?? "—"}
                        {item.nearest_shelter_distance_km != null && ` (${item.nearest_shelter_distance_km} km)`}
                      </span>
                    </div>
                  </div>
                  <div className="bg-slate-50 border border-slate-100 rounded-xl p-2.5">
                    <span className="text-slate-400 uppercase tracking-wider block mb-0.5 flex items-center space-x-1">
                      <HeartPulse className="w-3 h-3" /> <span>Nearest hospital</span>
                    </span>
                    <span className="text-slate-700">
                      {item.nearest_hospital_name ?? "—"}
                      {item.nearest_hospital_distance_km != null && ` (${item.nearest_hospital_distance_km} km)`}
                    </span>
                  </div>
                </div>

                {!item.accessibility_data_available && (
                  <p className="text-[10px] text-slate-400 italic">
                    No coordinates available for this disaster or nearby assets — accessibility defaulted to neutral (50).
                  </p>
                )}
              </motion.div>
            ))
          ) : (
            <div className="bg-white border border-slate-200 border-dashed rounded-2xl p-12 text-center text-slate-400 text-xs">
              <Navigation className="w-12 h-12 text-slate-300 mx-auto mb-3 animate-pulse" />
              <span>No active disasters to rank.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export const PriorityRanking: React.FC = () => {
  const [tab, setTab] = useState<TabKey>("need");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-slate-800">Priority Ranking</h2>
        <p className="text-xs text-slate-400">
          Two explainable, computed rankings of active disasters — how badly each needs help, and
          where limited resources should go first given both urgency and reachability.
        </p>
      </div>

      <div className="flex space-x-1 bg-slate-100 p-1 rounded-xl w-fit">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition ${
              tab === t.key ? "bg-white text-slate-800 shadow-sm" : "text-slate-500 hover:text-slate-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "need" ? <NeedScoreView /> : <DistributionPriorityView />}
    </div>
  );
};
