import React, { useState } from "react";
import { api, formatApiError } from "../lib/api";

interface PriorityResult {
  allocation_priority: string;
  confidence: number;
  recommended_relief_units: number;
}

export const AIPrediction: React.FC = () => {
  const [incidentId, setIncidentId] = useState("INC-24081");
  const [location, setLocation] = useState("Cuddalore Sector 2");
  const [disasterType, setDisasterType] = useState("Flood");
  const [severity, setSeverity] = useState("High");

  const [population, setPopulation] = useState(8309);
  const [households, setHouseholds] = useState(1729);
  const [damageScore, setDamageScore] = useState(49.5);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PriorityResult | null>({
    allocation_priority: "HIGH",
    confidence: 0.76,
    recommended_relief_units: 3953,
  });

  const handleAssess = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await api.post("/prediction/predict-priority", {
        population_affected: population,
        households_affected: households,
        infrastructure_damage_score: damageScore,
        disaster_type: disasterType,
        severity_level: severity,
      });

      if (res.data.success) {
        setResult(res.data.data);
      } else {
        setError(res.data.message || "Assessment failed.");
      }
    } catch (err: unknown) {
      console.error(err);
      setError(formatApiError(err, "Failed to run decision assessment."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4 font-sans text-[#172033]">
      
      {/* Header */}
      <div className="bg-white border border-[#E4E7EC] rounded-md p-3.5 flex items-center justify-between">
        <div>
          <h1 className="text-sm font-bold text-[#172033]">AI Decision Support</h1>
          <p className="text-[11px] text-[#667085]">
            Operational priority evaluation and relief unit estimation engine
          </p>
        </div>
        <span className="text-[10px] font-mono text-[#667085]">REASSESS FREQUENCY: REAL-TIME</span>
      </div>

      <div className="grid gap-4 lg:grid-cols-12">
        
        {/* Left Inputs Pane (5 cols) */}
        <div className="lg:col-span-5 bg-white border border-[#E4E7EC] rounded-md p-4 space-y-4">
          <div className="border-b border-[#E4E7EC] pb-2 text-xs font-bold text-[#172033]">
            Incident Telemetry Parameters
          </div>

          <form onSubmit={handleAssess} className="space-y-3 text-xs">
            <div>
              <label className="block text-[11px] font-semibold text-[#667085] mb-1">Target Incident Ref</label>
              <input
                type="text"
                value={incidentId}
                onChange={(e) => setIncidentId(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-[#F7F8FA] border border-[#E4E7EC] rounded font-mono font-semibold"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-[#667085] mb-1">Location Zone</label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-[#F7F8FA] border border-[#E4E7EC] rounded font-medium"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[11px] font-semibold text-[#667085] mb-1">Disaster Type</label>
                <select
                  value={disasterType}
                  onChange={(e) => setDisasterType(e.target.value)}
                  className="w-full px-2 py-1.5 bg-[#F7F8FA] border border-[#E4E7EC] rounded font-medium"
                >
                  <option value="Flood">Flood</option>
                  <option value="Cyclone">Cyclone</option>
                  <option value="Earthquake">Earthquake</option>
                  <option value="Tsunami">Tsunami</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-[#667085] mb-1">Severity Level</label>
                <select
                  value={severity}
                  onChange={(e) => setSeverity(e.target.value)}
                  className="w-full px-2 py-1.5 bg-[#F7F8FA] border border-[#E4E7EC] rounded font-medium"
                >
                  <option value="Critical">Critical</option>
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 pt-1">
              <div>
                <label className="block text-[10px] font-semibold text-[#667085] mb-1">Population</label>
                <input
                  type="number"
                  value={population}
                  onChange={(e) => setPopulation(parseInt(e.target.value) || 0)}
                  className="w-full px-2 py-1 bg-[#F7F8FA] border border-[#E4E7EC] rounded font-mono font-semibold text-xs"
                />
              </div>

              <div>
                <label className="block text-[10px] font-semibold text-[#667085] mb-1">Households</label>
                <input
                  type="number"
                  value={households}
                  onChange={(e) => setHouseholds(parseInt(e.target.value) || 0)}
                  className="w-full px-2 py-1 bg-[#F7F8FA] border border-[#E4E7EC] rounded font-mono font-semibold text-xs"
                />
              </div>

              <div>
                <label className="block text-[10px] font-semibold text-[#667085] mb-1">Damage Score</label>
                <input
                  type="number"
                  value={damageScore}
                  onChange={(e) => setDamageScore(parseFloat(e.target.value) || 0)}
                  className="w-full px-2 py-1 bg-[#F7F8FA] border border-[#E4E7EC] rounded font-mono font-semibold text-xs"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold text-xs rounded transition-colors"
            >
              {loading ? "Computing Assessment..." : "Run Assessment"}
            </button>
          </form>
        </div>

        {/* Right Decision Results Pane (7 cols) */}
        <div className="lg:col-span-7 bg-white border border-[#E4E7EC] rounded-md p-4 space-y-4">
          <div className="border-b border-[#E4E7EC] pb-2 flex items-center justify-between text-xs">
            <span className="font-bold text-[#172033]">Evaluation Result</span>
            <span className="text-[10px] font-mono text-[#667085]">DECISION REF: DEC-9021</span>
          </div>

          {error ? (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded">
              {error}
            </div>
          ) : result ? (
            <div className="space-y-4 text-xs">
              
              {/* Main Metrics Strip */}
              <div className="grid grid-cols-3 gap-3 p-3 bg-slate-50 border border-[#E4E7EC] rounded">
                <div>
                  <span className="text-[10px] uppercase font-bold text-[#667085] block">Priority</span>
                  <span className="text-base font-bold text-red-700 uppercase">{result.allocation_priority}</span>
                </div>

                <div>
                  <span className="text-[10px] uppercase font-bold text-[#667085] block">Relief Units</span>
                  <span className="text-base font-mono font-bold text-[#172033]">{result.recommended_relief_units.toLocaleString()}</span>
                </div>

                <div>
                  <span className="text-[10px] uppercase font-bold text-[#667085] block">Confidence</span>
                  <span className="text-base font-mono font-bold text-blue-700">{Math.round(result.confidence * 100)}%</span>
                </div>
              </div>

              {/* Why This Priority */}
              <div className="space-y-1.5">
                <h3 className="font-bold text-[#172033] text-xs uppercase tracking-wider text-[#667085]">
                  WHY THIS PRIORITY
                </h3>
                <ul className="space-y-1 text-[11px] text-[#172033] bg-slate-50 p-3 rounded border border-[#E4E7EC]">
                  <li className="flex items-center space-x-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span>High affected population density ({population.toLocaleString()} citizens).</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span>Infrastructure damage index recorded at {damageScore}/100.</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span>Submerged primary access road delaying initial ground convoy.</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <span className="text-blue-600 font-bold">•</span>
                    <span>Shelter capacity in immediate radius operating near maximum threshold.</span>
                  </li>
                </ul>
              </div>

              {/* Recommended Action */}
              <div className="space-y-1.5">
                <h3 className="font-bold text-[#172033] text-xs uppercase tracking-wider text-[#667085]">
                  RECOMMENDED ACTION
                </h3>
                <div className="p-3 bg-blue-50/60 border border-blue-200 rounded space-y-1 text-[11px] text-blue-900">
                  <div className="font-bold">1. Dispatch {result.recommended_relief_units.toLocaleString()} Relief Units via Bypass Arterial Expressway.</div>
                  <div className="font-bold">2. Deploy 2 mobile medical teams to Cuddalore Sector 2.</div>
                  <div className="font-bold">3. Review secondary shelter capacity at Red Cross Field Unit.</div>
                </div>
              </div>

            </div>
          ) : (
            <div className="text-center py-10 text-[#667085] text-xs">
              Select an incident and run assessment to evaluate priority decision.
            </div>
          )}
        </div>

      </div>

    </div>
  );
};
