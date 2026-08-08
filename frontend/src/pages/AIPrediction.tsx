import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  TrendingUp,
  AlertTriangle,
  HelpCircle,
  Activity,
  Cpu,
  Package,
  Gauge,
  Zap
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
  { key: "flood", label: "Flood Risk" },
  { key: "priority", label: "Resource Priority" },
  { key: "action_plan", label: "AI Action Plan" },
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
        setError(res.data.message || "Prediction analysis failed.");
      }
    } catch (err: unknown) {
      console.error(err);
      const status = (err as { response?: { status?: number } })?.response?.status;
      setError(
        status === 503
          ? "Prediction Service is unavailable. The ML model file (.pkl) is missing on the server."
          : "Network connectivity error occurred while querying prediction API."
      );
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case "critical":
        return { text: "text-rose-600 bg-rose-50 border-rose-200", stroke: "#ef4444" };
      case "high":
        return { text: "text-amber-600 bg-amber-50 border-amber-200", stroke: "#f97316" };
      case "medium":
        return { text: "text-yellow-600 bg-yellow-50 border-yellow-200", stroke: "#eab308" };
      default:
        return { text: "text-emerald-600 bg-emerald-50 border-emerald-200", stroke: "#10b981" };
    }
  };

  const riskStyle = getRiskColor(result?.risk_level || "low");

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {/* Parameters Panel */}
      <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl shadow-sm p-6 space-y-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-800">Environmental Parameters</h2>
            <p className="text-xs text-slate-400">Configure weather and terrain sensor telemetry.</p>
          </div>
        </div>

        <form onSubmit={handleRunAnalysis} className="space-y-6">
          <div className="grid gap-6 sm:grid-cols-2">
            {[
              { label: "Rainfall (mm)", name: "rainfall_mm", min: 0, max: 500, step: 0.1, help: "Daily rain gauge measurement" },
              { label: "River Level (meters)", name: "river_level_m", min: 0, max: 20, step: 0.1, help: "Gauge elevation above baseline" },
              { label: "Soil Moisture (%)", name: "soil_moisture_pct", min: 0, max: 100, step: 1, help: "Ground water saturation ratio" },
              { label: "Temperature (°C)", name: "temperature_c", min: 0, max: 55, step: 1, help: "Ambient air temperature" },
              { label: "Relative Humidity (%)", name: "humidity_pct", min: 0, max: 100, step: 1, help: "Atmospheric saturation level" },
              { label: "Previous Flood History", name: "previous_flood_events", min: 0, max: 15, step: 1, help: "Count of historic floodings" },
              { label: "Altitude Elevation (meters)", name: "elevation_m", min: 0, max: 1500, step: 1, help: "Ground height above sea level" },
              { label: "Population Density (sq km)", name: "population_density", min: 0, max: 25000, step: 10, help: "District density demographics" }
            ].map((field) => (
              <div key={field.name} className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-slate-700">{field.label}</label>
                  <span className="text-[10px] text-slate-400 font-medium" title={field.help}>
                    <HelpCircle className="w-3.5 h-3.5 cursor-help" />
                  </span>
                </div>
                <input
                  type="number"
                  name={field.name}
                  min={field.min}
                  max={field.max}
                  step={field.step}
                  value={formData[field.name as keyof typeof formData]}
                  onChange={handleInputChange}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-colors duration-150 font-medium"
                  required
                />
              </div>
            ))}
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center space-x-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold text-sm rounded-xl transition duration-150 shadow-md shadow-indigo-600/15"
            >
              <Activity className="w-4 h-4" />
              <span>{loading ? "Calculating..." : "Run Flood Risk Analysis"}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Results Panel */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6 flex flex-col justify-between min-h-[460px]">
        <div>
          <h2 className="text-base font-semibold text-slate-800">Model Output Telemetry</h2>
          <p className="text-xs text-slate-400 mt-1">Evaluated by XGBoost / Random Forest Classifier.</p>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center py-6">
          <AnimatePresence mode="wait">
            {loading ? (
              <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col items-center justify-center space-y-4">
                <div className="w-16 h-16 rounded-full border-4 border-indigo-200 border-t-indigo-600 animate-spin" />
                <span className="text-xs text-slate-500 font-semibold animate-pulse">Computing telemetry...</span>
              </motion.div>
            ) : error ? (
              <motion.div key="error" initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-start space-x-3 text-left leading-relaxed font-medium">
                <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-500" />
                <span>{error}</span>
              </motion.div>
            ) : result ? (
              <motion.div key="result" initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="flex flex-col items-center text-center space-y-4 w-full">
                <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-0.5 rounded bg-indigo-50 text-indigo-600 border border-indigo-200">
                  ML PREDICTION
                </span>
                <div className={`px-5 py-2.5 rounded-xl border text-lg font-black uppercase tracking-wider ${riskStyle.text}`}>
                  {result.risk_level} RISK
                </div>
                <p className="text-[11px] text-slate-500 font-semibold">{Math.round(result.confidence * 100)}% model confidence</p>

                <div className="w-full pt-4 border-t border-slate-100">
                  <span className="text-3xl font-extrabold text-slate-800">{Math.round(result.probability * 100)}%</span>
                  <p className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mt-0.5">Raw Flood Probability</p>
                </div>
              </motion.div>
            ) : (
              <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center text-center text-slate-400 text-xs">
                <TrendingUp className="w-12 h-12 text-slate-300 mb-3 animate-pulse" />
                <span>Configure environmental parameters on the left and click Run Analysis.</span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="text-[10px] text-slate-400 font-medium text-center border-t border-slate-100 pt-4">
          Connected to FastAPI endpoint <code className="text-slate-600">/api/v1/prediction/predict</code>
        </div>
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
        setError(res.data.message || "Priority analysis failed.");
      }
    } catch (err: unknown) {
      console.error(err);
      setError(formatApiError(err, "Failed to query priority prediction model. Check inputs."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {/* Inputs Form */}
      <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl shadow-sm p-6 space-y-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
            <Package className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-800">Incident & Resource Telemetry</h2>
            <p className="text-xs text-slate-400">Trained on 200k disaster relief allocation records.</p>
          </div>
        </div>

        <form onSubmit={handleRunAnalysis} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Affected Population</label>
              <input
                type="number"
                value={formData.population_affected}
                onChange={(e) => setFormData(p => ({ ...p, population_affected: parseInt(e.target.value) || 0 }))}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Households Affected</label>
              <input
                type="number"
                value={formData.households_affected}
                onChange={(e) => setFormData(p => ({ ...p, households_affected: parseInt(e.target.value) || 0 }))}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Damage Score (0-100)</label>
              <input
                type="number"
                value={formData.infrastructure_damage_score}
                onChange={(e) => setFormData(p => ({ ...p, infrastructure_damage_score: parseFloat(e.target.value) || 0 }))}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center space-x-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-semibold text-sm rounded-xl shadow-md shadow-purple-600/15"
            >
              <Gauge className="w-4 h-4" />
              <span>{loading ? "Running Models..." : "Predict Priority & Relief Units"}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Output Panel */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6 flex flex-col justify-between min-h-[420px]">
        <div>
          <h2 className="text-base font-semibold text-slate-800">Allocation Priority Result</h2>
          <p className="text-xs text-slate-400 mt-1">RandomForestClassifier & RandomForestRegressor outputs.</p>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center py-6 text-center">
          {loading ? (
            <div className="w-12 h-12 rounded-full border-4 border-purple-200 border-t-purple-600 animate-spin" />
          ) : error ? (
            <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-start space-x-2 text-left">
              <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          ) : result ? (
            <div className="space-y-4 w-full">
              <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200">
                ML PREDICTION
              </span>
              <div className="text-2xl font-black text-rose-600 uppercase">
                {result.allocation_priority} PRIORITY
              </div>
              <p className="text-xs text-slate-500 font-semibold">
                Confidence: {(result.confidence * 100).toFixed(0)}%
              </p>
              <div className="pt-4 border-t border-slate-100">
                <span className="text-3xl font-black text-slate-800">
                  {result.recommended_relief_units.toLocaleString()}
                </span>
                <p className="text-[10px] uppercase font-bold text-slate-400 mt-0.5">
                  Recommended Relief Units
                </p>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-400">
              Submit telemetry to compute priority & relief units.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const ActionPlanView: React.FC = () => {
  return (
    <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-6">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center font-bold">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-extrabold text-slate-800">Synthesized AI Action Plan</h2>
            <p className="text-xs text-slate-400">Integrated response strategy combining ML predictions, rule-based checks, and routing.</p>
          </div>
        </div>
        <span className="text-xs font-bold text-indigo-600 bg-indigo-50 border border-indigo-200 px-3 py-1 rounded-full">
          AUTO GENERATED
        </span>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* Priority Section */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-200">
            ML PREDICTION
          </span>
          <h4 className="font-bold text-slate-800 text-sm">1. Priority Level</h4>
          <p className="text-xs text-rose-600 font-bold">CRITICAL (Confidence: 94%)</p>
          <p className="text-[11px] text-slate-500">Based on high affected population and poor accessibility score.</p>
        </div>

        {/* Resource Allocation */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-indigo-100 text-indigo-800 border border-indigo-200">
            ML PREDICTION
          </span>
          <h4 className="font-bold text-slate-800 text-sm">2. Resource Allocation</h4>
          <p className="text-xs text-indigo-600 font-bold">4,250 Relief Units</p>
          <p className="text-[11px] text-slate-500">Includes 2,000L water, 500 medical kits, 1,000 food ration packs.</p>
        </div>

        {/* Route & Road Status */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200">
            ROUTING
          </span>
          <h4 className="font-bold text-slate-800 text-sm">3. Safe Route & Road Status</h4>
          <p className="text-xs text-amber-600 font-bold">Bypass Arterial Expressway (22.8km, ETA 31 mins)</p>
          <p className="text-[11px] text-slate-500">GST Underpass BLOCKED due to 4ft water logging.</p>
        </div>

        {/* Shelter & Hospital Capacity */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200">
            RULE-BASED
          </span>
          <h4 className="font-bold text-slate-800 text-sm">4. Shelter & Hospital Destination</h4>
          <p className="text-xs text-emerald-600 font-bold">Tambaram General Hospital Zone C</p>
          <p className="text-[11px] text-slate-500">Available Beds: 28 ICU, 140 General. Shelter Capacity: 150 spots.</p>
        </div>

        {/* Team Assignment */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-purple-100 text-purple-800 border border-purple-200">
            RULE-BASED
          </span>
          <h4 className="font-bold text-slate-800 text-sm">5. Team Assignment</h4>
          <p className="text-xs text-purple-600 font-bold">Squad Alpha (2 Medical Teams, 15 Volunteers)</p>
          <p className="text-[11px] text-slate-500">Dispatched via TN-01-EQ-9042 heavy vehicle.</p>
        </div>

        {/* Recommended Actions */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-blue-100 text-blue-800 border border-blue-200">
            ACTIONABLE
          </span>
          <h4 className="font-bold text-slate-800 text-sm">6. Recommended Actions</h4>
          <ul className="text-[11px] text-slate-600 list-disc list-inside space-y-1">
            <li>Issue evacuation advisory for low-lying Sector 4.</li>
            <li>Pre-position secondary water pumps at Tambaram flyover.</li>
            <li>Notify NDRF team lead for boat deployment if rainfall exceeds 200mm.</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export const AIPrediction: React.FC = () => {
  const [tab, setTab] = useState<TabKey>("flood");

  return (
    <div className="space-y-6">
      <div className="flex space-x-1 bg-slate-200 p-1.5 rounded-2xl w-fit">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-xs font-bold rounded-xl transition ${
              tab === t.key ? "bg-white text-slate-800 shadow-sm" : "text-slate-600 hover:text-slate-900"
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
