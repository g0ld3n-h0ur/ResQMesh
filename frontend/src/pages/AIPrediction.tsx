import React, { useState } from "react";
import { AnimatePresence } from "framer-motion";
import {
  TrendingUp,
  AlertTriangle,
  Cpu,
  Package,
  Gauge,
  Zap,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Sliders,
  ShieldCheck
} from "lucide-react";
import { api, formatApiError } from "../lib/api";

interface FloodPredictionResult {
  prediction: number;
  confidence: number;
  risk_level: string;
  probability: number;
  model: string;
}

interface PriorityPredictionResult {
  allocation_priority: string;
  confidence: number;
  class_probabilities: Record<string, number>;
  recommended_relief_units: number;
  priority_model: string;
  relief_units_model: string;
}

const TABS = [
  { key: "flood", label: "Flood Risk Assessment" },
  { key: "priority", label: "Resource Allocation Priority" },
  { key: "action_plan", label: "Operational Action Plan" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

const FloodPredictionView: React.FC = () => {
  const [formData, setFormData] = useState({
    rainfall_mm: 150,
    river_level_m: 5.2,
    soil_moisture_pct: 75,
    temperature_c: 28,
    humidity_pct: 85,
    previous_flood_events: 2,
    elevation_m: 12,
    population_density: 3500
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FloodPredictionResult | null>(null);
  const [showTechDetails, setShowTechDetails] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: parseFloat(value) || 0
    }));
  };

  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.post("/prediction/predict", {
        prediction_type: "flood",
        ...formData
      });
      if (res.data.success) {
        setResult(res.data.data);
      } else {
        setError(res.data.message || "Risk assessment failed.");
      }
    } catch (err: unknown) {
      console.error(err);
      setError(formatApiError(err, "Network connectivity error occurred while querying decision support API."));
    } finally {
      setLoading(false);
    }
  };

  const getRiskBadge = (level: string) => {
    switch (level?.toLowerCase()) {
      case "critical":
        return "bg-rose-100 text-rose-800 border-rose-200";
      case "high":
        return "bg-amber-100 text-amber-800 border-amber-200";
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      default:
        return "bg-emerald-100 text-emerald-800 border-emerald-200";
    }
  };

  return (
    <div className="grid gap-5 lg:grid-cols-12 font-sans">
      {/* Parameters Panel (7 cols) */}
      <div className="lg:col-span-7 bg-white border border-slate-200 rounded-xl p-5 shadow-2xs space-y-4">
        <div className="flex items-center space-x-2.5 border-b border-slate-100 pb-3">
          <div className="p-2 rounded-lg bg-slate-100 text-slate-700">
            <Sliders className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs uppercase font-bold text-slate-800 tracking-wider">Telemetry Inputs</h2>
            <p className="text-[11px] text-slate-500">Configure weather sensor & terrain measurements.</p>
          </div>
        </div>

        <form onSubmit={handleRunAnalysis} className="space-y-4">
          <div className="grid gap-3.5 sm:grid-cols-2 text-xs">
            {[
              { label: "Rainfall (mm)", name: "rainfall_mm", min: 0, max: 500, step: 0.1 },
              { label: "River Level (m)", name: "river_level_m", min: 0, max: 20, step: 0.1 },
              { label: "Soil Moisture (%)", name: "soil_moisture_pct", min: 0, max: 100, step: 1 },
              { label: "Temperature (°C)", name: "temperature_c", min: 0, max: 55, step: 1 },
              { label: "Relative Humidity (%)", name: "humidity_pct", min: 0, max: 100, step: 1 },
              { label: "Historic Flood Count", name: "previous_flood_events", min: 0, max: 15, step: 1 },
              { label: "Elevation (m)", name: "elevation_m", min: 0, max: 1500, step: 1 },
              { label: "Population Density (sq km)", name: "population_density", min: 0, max: 25000, step: 10 }
            ].map((field) => (
              <div key={field.name} className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-700 block">{field.label}</label>
                <input
                  type="number"
                  name={field.name}
                  min={field.min}
                  max={field.max}
                  step={field.step}
                  value={formData[field.name as keyof typeof formData]}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-800"
                  required
                />
              </div>
            ))}
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-end">
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white font-bold text-xs rounded-lg shadow-2xs flex items-center space-x-2 transition-colors"
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>{loading ? "Computing Risk Assessment..." : "Evaluate Flood Risk"}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Decision Panel (5 cols) */}
      <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl shadow-2xs p-5 flex flex-col justify-between space-y-4">
        <div>
          <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
            <ShieldCheck className="w-4 h-4 text-indigo-600" />
            <h2 className="text-xs uppercase font-bold text-slate-800 tracking-wider">Risk Evaluation Decision</h2>
          </div>
          <p className="text-[11px] text-slate-500 mt-1.5">Actionable risk assessment for emergency dispatch commanders.</p>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center py-4">
          <AnimatePresence mode="wait">
            {loading ? (
              <div className="flex flex-col items-center justify-center space-y-3">
                <div className="w-10 h-10 rounded-full border-3 border-slate-200 border-t-slate-800 animate-spin" />
                <span className="text-xs text-slate-500 font-semibold">Evaluating sensor telemetry...</span>
              </div>
            ) : error ? (
              <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg flex items-start space-x-2 text-left font-medium">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            ) : result ? (
              <div className="space-y-4 text-center w-full">
                <div className="inline-block">
                  <span className={`px-4 py-1.5 rounded-full border text-sm font-extrabold uppercase tracking-wider ${getRiskBadge(result.risk_level)}`}>
                    {result.risk_level} RISK LEVEL
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-left pt-2">
                  <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg">
                    <span className="text-[10px] text-slate-400 font-bold uppercase block">Flood Probability</span>
                    <span className="text-xl font-mono font-bold text-slate-900">{Math.round(result.probability * 100)}%</span>
                  </div>
                  <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg">
                    <span className="text-[10px] text-slate-400 font-bold uppercase block">Assessment Confidence</span>
                    <span className="text-xl font-mono font-bold text-indigo-700">{Math.round(result.confidence * 100)}%</span>
                  </div>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-left text-xs space-y-1">
                  <span className="font-bold text-slate-800 block">Recommended Command Action:</span>
                  <p className="text-slate-600 text-[11px] leading-relaxed">
                    {result.prediction === 1
                      ? "High probability of inundation. Issue immediate evacuation notice for low-lying zones and pre-position water pumps."
                      : "Risk level within manageable threshold. Maintain standard weather monitoring."}
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center text-slate-400 text-xs py-8">
                <TrendingUp className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                <span>Submit telemetry inputs on the left to evaluate flood risk.</span>
              </div>
            )}
          </AnimatePresence>
        </div>

        {/* Collapsible Tech Details */}
        {result && (
          <div className="border-t border-slate-100 pt-3">
            <button
              onClick={() => setShowTechDetails(prev => !prev)}
              className="text-[10px] text-slate-500 font-semibold flex items-center justify-between w-full hover:text-slate-800"
            >
              <span>Technical evaluation telemetry</span>
              {showTechDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>

            {showTechDetails && (
              <div className="mt-2 text-[10px] font-mono text-slate-500 bg-slate-50 p-2 rounded border border-slate-200 space-y-1">
                <div>Model Ref: {result.model}</div>
                <div>Raw Probability Value: {result.probability}</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const PriorityPredictionView: React.FC = () => {
  const [formData, setFormData] = useState({
    population_affected: 8309,
    households_affected: 1729,
    infrastructure_damage_score: 49.5,
    nearest_relief_center_distance_km: 14.25,
    available_volunteers: 27,
    medical_teams_available: 2,
    food_stock_kg: 210.0,
    water_stock_liters: 1725.0,
    shelter_capacity: 292.0,
    funding_available_usd: 46534.98,
    vulnerability_index: 0.277,
    ngo_present: true,
    government_response_active: true,
    disaster_type: "Flood",
    severity_level: "High",
    accessibility_status: "Accessible",
    communication_status: "Full",
    power_status: "Partial",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PriorityPredictionResult | null>(null);

  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.post("/prediction/predict-priority", formData);
      if (res.data.success) {
        setResult(res.data.data);
      } else {
        setError(res.data.message || "Priority evaluation failed.");
      }
    } catch (err: unknown) {
      console.error(err);
      setError(formatApiError(err, "Failed to evaluate priority decision. Check inputs."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-5 lg:grid-cols-12 font-sans">
      {/* Inputs Form */}
      <div className="lg:col-span-7 bg-white border border-slate-200 rounded-xl shadow-2xs p-5 space-y-4">
        <div className="flex items-center space-x-2.5 border-b border-slate-100 pb-3">
          <div className="p-2 rounded-lg bg-slate-100 text-slate-700">
            <Package className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs uppercase font-bold text-slate-800 tracking-wider">Incident Telemetry</h2>
            <p className="text-[11px] text-slate-500">Provide field demographics & resource stocks.</p>
          </div>
        </div>

        <form onSubmit={handleRunAnalysis} className="space-y-4">
          <div className="grid gap-3.5 sm:grid-cols-3 text-xs">
            <div>
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">Affected Population</label>
              <input
                type="number"
                value={formData.population_affected}
                onChange={(e) => setFormData(p => ({ ...p, population_affected: parseInt(e.target.value) || 0 }))}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-semibold"
              />
            </div>
            <div>
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">Households Affected</label>
              <input
                type="number"
                value={formData.households_affected}
                onChange={(e) => setFormData(p => ({ ...p, households_affected: parseInt(e.target.value) || 0 }))}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-semibold"
              />
            </div>
            <div>
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">Damage Score (0-100)</label>
              <input
                type="number"
                value={formData.infrastructure_damage_score}
                onChange={(e) => setFormData(p => ({ ...p, infrastructure_damage_score: parseFloat(e.target.value) || 0 }))}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-semibold"
              />
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-end">
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white font-bold text-xs rounded-lg shadow-2xs flex items-center space-x-2 transition-colors"
            >
              <Gauge className="w-3.5 h-3.5" />
              <span>{loading ? "Evaluating Priority..." : "Evaluate Allocation Priority"}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Output Panel */}
      <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl shadow-2xs p-5 flex flex-col justify-between space-y-4">
        <div>
          <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
            <CheckCircle2 className="w-4 h-4 text-indigo-600" />
            <h2 className="text-xs uppercase font-bold text-slate-800 tracking-wider">Priority Decision Output</h2>
          </div>
          <p className="text-[11px] text-slate-500 mt-1.5">Actionable priority rank & recommended relief units.</p>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center py-4 text-center">
          {loading ? (
            <div className="w-10 h-10 rounded-full border-3 border-slate-200 border-t-slate-800 animate-spin" />
          ) : error ? (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg text-left">
              <span>{error}</span>
            </div>
          ) : result ? (
            <div className="space-y-4 w-full text-left">
              <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl space-y-2">
                <span className="text-[10px] text-slate-400 font-bold uppercase block">Allocation Priority</span>
                <div className="text-xl font-black text-rose-600 uppercase tracking-wide">
                  {result.allocation_priority} PRIORITY
                </div>
                <span className="text-[11px] text-slate-500 font-semibold block">
                  Evaluation Confidence: {(result.confidence * 100).toFixed(0)}%
                </span>
              </div>

              <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl">
                <span className="text-[10px] text-slate-400 font-bold uppercase block">Recommended Relief Units</span>
                <span className="text-2xl font-black text-slate-900 font-mono">
                  {result.recommended_relief_units.toLocaleString()} Units
                </span>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-400">
              Submit telemetry to evaluate priority & recommended relief units.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const ActionPlanView: React.FC = () => {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs space-y-5 font-sans">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-slate-900 text-white font-bold">
            <Zap className="w-4 h-4 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">Synthesized Operational Action Plan</h2>
            <p className="text-[11px] text-slate-500">Integrated response strategy combining telemetry, capacity & routing.</p>
          </div>
        </div>
        <span className="text-[10px] font-bold text-slate-700 bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-lg uppercase">
          OPERATIONAL DISPATCH
        </span>
      </div>

      <div className="grid gap-3.5 md:grid-cols-2 lg:grid-cols-3 text-xs">
        <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
          <span className="text-[10px] font-bold text-rose-700 uppercase block">1. Priority Ranking</span>
          <h4 className="font-bold text-slate-900">CRITICAL PRIORITY</h4>
          <p className="text-slate-600 text-[11px] leading-relaxed">Based on high affected population and blocked primary route access.</p>
        </div>

        <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
          <span className="text-[10px] font-bold text-indigo-700 uppercase block">2. Resource Allocation</span>
          <h4 className="font-bold text-slate-900">4,250 Relief Units</h4>
          <p className="text-slate-600 text-[11px] leading-relaxed">2,000L water, 500 medical kits, 1,000 food ration packs.</p>
        </div>

        <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
          <span className="text-[10px] font-bold text-amber-700 uppercase block">3. Safe Route Dispatch</span>
          <h4 className="font-bold text-slate-900">Bypass Arterial Expressway</h4>
          <p className="text-slate-600 text-[11px] leading-relaxed">22.8km distance, ETA 31 mins (GST Underpass Blocked).</p>
        </div>

        <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
          <span className="text-[10px] font-bold text-emerald-700 uppercase block">4. Target Shelter & Hospital</span>
          <h4 className="font-bold text-slate-900">Tambaram General Hospital Zone C</h4>
          <p className="text-slate-600 text-[11px] leading-relaxed">28 ICU Beds, 140 General Beds, 150 Shelter Spots.</p>
        </div>

        <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
          <span className="text-[10px] font-bold text-purple-700 uppercase block">5. Squad Assignment</span>
          <h4 className="font-bold text-slate-900">Squad Alpha (15 Volunteers)</h4>
          <p className="text-slate-600 text-[11px] leading-relaxed">Assigned to medical triage and cargo offloading.</p>
        </div>

        <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
          <span className="text-[10px] font-bold text-slate-700 uppercase block">6. Actionable Directives</span>
          <ul className="text-[11px] text-slate-600 space-y-0.5 list-disc list-inside">
            <li>Issue evacuation notice for Sector 4.</li>
            <li>Pre-position water pumps at Tambaram.</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export const AIPrediction: React.FC = () => {
  const [tab, setTab] = useState<TabKey>("flood");

  return (
    <div className="space-y-4 font-sans">
      <div className="flex space-x-1 bg-slate-200/80 p-1 rounded-xl w-fit">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-3.5 py-1.5 text-xs font-bold rounded-lg transition ${
              tab === t.key ? "bg-white text-slate-900 shadow-2xs" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "flood" && <FloodPredictionView />}
      {tab === "priority" && <PriorityPredictionView />}
      {tab === "action_plan" && <ActionPlanView />}
    </div>
  );
};
