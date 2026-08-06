import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  TrendingUp, 
  AlertTriangle, 
  HelpCircle,
  Activity,
  Cpu
} from "lucide-react";
import { api } from "../lib/api";

interface PredictionResult {
  prediction: number;
  confidence: number;
  risk_level: string;
  probability: number;
  model: string;
}

export const AIPrediction: React.FC = () => {
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
  const [result, setResult] = useState<PredictionResult | null>(null);

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
    } catch (err: any) {
      console.error(err);
      setError(
        err.response?.status === 503
          ? "Prediction Service is unavailable. The ML model file (.pkl) is missing on the server. Please run the training script backend/ml/train_sensor_model.py."
          : "Network connectivity error occurred while querying prediction API."
      );
    } finally {
      setLoading(false);
    }
  };

  // Determine risk details
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
              <TrendingUp className="w-4 h-4" />
              <span>{loading ? "Calculating Risk Model..." : "Run EOC Risk Analysis"}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Results View */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6 flex flex-col justify-between min-h-[460px]">
        <div>
          <h2 className="text-base font-semibold text-slate-800">Risk Prognosis</h2>
          <p className="text-xs text-slate-400 mt-1">Calculated probability report returned by AI service.</p>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center py-6">
          <AnimatePresence mode="wait">
            {loading ? (
              <motion.div 
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center justify-center space-y-4"
              >
                <div className="w-16 h-16 rounded-full border-4 border-indigo-200 border-t-indigo-600 animate-spin" />
                <span className="text-xs text-slate-500 font-semibold animate-pulse">Running Neural Net...</span>
              </motion.div>
            ) : error ? (
              <motion.div 
                key="error"
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-start space-x-3 text-left leading-relaxed font-medium"
              >
                <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-500" />
                <span>{error}</span>
              </motion.div>
            ) : result ? (
              <motion.div 
                key="result"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="flex flex-col items-center text-center space-y-6 w-full"
              >
                {/* SVG Gauge */}
                <div className="relative w-40 h-40">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle
                      cx="80"
                      cy="80"
                      r="65"
                      stroke="#f1f5f9"
                      strokeWidth="10"
                      fill="transparent"
                    />
                    <circle
                      cx="80"
                      cy="80"
                      r="65"
                      stroke={riskStyle.stroke}
                      strokeWidth="10"
                      fill="transparent"
                      strokeDasharray={2 * Math.PI * 65}
                      strokeDashoffset={2 * Math.PI * 65 * (1 - result.probability)}
                      className="transition-all duration-1000 ease-out"
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-3xl font-extrabold text-slate-800">
                      {Math.round(result.probability * 100)}%
                    </span>
                    <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mt-0.5">
                      Flood Probability
                    </span>
                  </div>
                </div>

                {/* Risk Level Badge */}
                <div className={`px-4 py-2 rounded-xl border text-sm font-bold uppercase tracking-wider ${riskStyle.text}`}>
                  {result.risk_level} Risk Level
                </div>

                <p className="text-xs text-slate-600 px-4 font-medium leading-relaxed">
                  " {result.risk_level?.toLowerCase() === "critical" || result.risk_level?.toLowerCase() === "high" 
                    ? "Severe hazard alert: high likelihood of water intrusion and terrain pooling. Alert EOC responders."
                    : "Condition within margins. Continue routing standard patrols."} "
                </p>
              </motion.div>
            ) : (
              <motion.div 
                key="idle"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center text-center text-slate-400 text-xs"
              >
                <Activity className="w-12 h-12 text-slate-300 mb-3 animate-pulse" />
                <span>Submit telemetry input on left to run ML risk predictor.</span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Info label */}
        <div className="text-[10px] text-slate-400 font-medium text-center border-t border-slate-100 pt-4">
          Estimator: RandomForestRegressor model loaded from EOC filesystem.
        </div>
      </div>
    </div>
  );
};
