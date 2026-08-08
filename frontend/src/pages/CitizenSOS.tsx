import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, unwrapList, formatApiError } from "../lib/api";

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

export const CitizenSOS: React.FC = () => {
  const queryClient = useQueryClient();

  const [reporterName, setReporterName] = useState("");
  const [phone, setPhone] = useState("");
  const [disasterType, setDisasterType] = useState("Flood Inundation");
  const [address, setAddress] = useState("");
  const [description, setDescription] = useState("");

  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [locationMsg, setLocationMsg] = useState<string>("Click 'Detect Location' for GPS fix");

  const [formMsg, setFormMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const { data: reports = [], isLoading } = useQuery<EmergencyReport[]>({
    queryKey: ["sos-reports-list"],
    queryFn: async () => unwrapList<EmergencyReport>(await api.get("/reports/")),
    refetchInterval: 15_000,
  });

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      setLocationMsg("Geolocation API not supported by browser.");
      return;
    }

    setLocationMsg("Acquiring GPS fix...");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
        });
        setLocationMsg(`Fix Acquired: ${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`);
      },
      (err) => {
        console.error(err);
        setLocationMsg("GPS positioning failed. Enter location manually below.");
      }
    );
  };

  const createReportMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        reporter_name: reporterName || "Anonymous Resident",
        phone: phone || "9999999999",
        disaster_type: disasterType,
        latitude: coords?.lat ?? 12.9716,
        longitude: coords?.lng ?? 80.2452,
        address: address || "Chennai Coastal Area",
        description: description || "Immediate assistance requested.",
      };
      await api.post("/reports/emergency", payload);
    },
    onSuccess: () => {
      setFormMsg({ type: "success", text: "Distress signal transmitted to emergency control center." });
      setReporterName("");
      setPhone("");
      setAddress("");
      setDescription("");
      queryClient.invalidateQueries({ queryKey: ["sos-reports-list"] });
    },
    onError: (err: unknown) => {
      setFormMsg({ type: "error", text: formatApiError(err, "Failed to transmit distress report.") });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormMsg(null);
    createReportMutation.mutate();
  };

  return (
    <div className="space-y-4 font-sans text-[#172033]">
      
      {/* Header */}
      <div className="bg-white border border-[#E4E7EC] rounded-md p-3.5 flex items-center justify-between">
        <div>
          <h1 className="text-sm font-bold text-[#172033]">Citizen Emergency SOS Beacon</h1>
          <p className="text-[11px] text-[#667085]">
            Submit high-priority distress reports directly to local emergency response teams.
          </p>
        </div>
        <span className="text-[10px] font-mono text-red-700 bg-red-50 border border-red-200 px-2 py-0.5 rounded font-bold">
          PRIORITY CHANNEL
        </span>
      </div>

      <div className="grid gap-4 lg:grid-cols-12">
        
        {/* Distress Signal Form (5 cols) */}
        <div className="lg:col-span-5 bg-white border border-[#E4E7EC] rounded-md p-4 space-y-3">
          <div className="border-b border-[#E4E7EC] pb-2 text-xs font-bold text-[#172033]">
            Submit Emergency Distress Signal
          </div>

          {formMsg && (
            <div className={`p-2.5 rounded text-xs border ${
              formMsg.type === "success"
                ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                : "bg-red-50 text-red-800 border-red-200"
            }`}>
              {formMsg.text}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3 text-xs">
            <div>
              <label className="block text-[11px] font-semibold text-[#667085] mb-1">Full Name</label>
              <input
                type="text"
                value={reporterName}
                onChange={(e) => setReporterName(e.target.value)}
                placeholder="e.g. Priya Sundaram"
                className="w-full px-2.5 py-1.5 bg-[#F7F8FA] border border-[#E4E7EC] rounded text-xs"
                required
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-[#667085] mb-1">Contact Phone</label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="e.g. +91 98400 12345"
                className="w-full px-2.5 py-1.5 bg-[#F7F8FA] border border-[#E4E7EC] rounded text-xs font-mono"
                required
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-[#667085] mb-1">Emergency Category</label>
              <select
                value={disasterType}
                onChange={(e) => setDisasterType(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-[#F7F8FA] border border-[#E4E7EC] rounded text-xs font-semibold"
              >
                <option value="Flood Inundation">Flood Inundation / Submerged House</option>
                <option value="Medical Emergency">Medical Emergency / Critical Trauma</option>
                <option value="Structural Collapse">Structural / Building Collapse</option>
                <option value="Food & Water Shortage">Food & Drinking Water Shortage</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-[11px] font-semibold text-[#667085]">Location / Address</label>
                <button
                  type="button"
                  onClick={handleGetLocation}
                  className="text-[10px] text-blue-600 underline font-semibold"
                >
                  Detect GPS
                </button>
              </div>
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="Door No, Street Name, Area"
                className="w-full px-2.5 py-1.5 bg-[#F7F8FA] border border-[#E4E7EC] rounded text-xs"
                required
              />
              <div className="text-[10px] text-[#667085] mt-1 font-mono">{locationMsg}</div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-[#667085] mb-1">Situation Details</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                placeholder="Describe trapped people, water level, urgent medical needs..."
                className="w-full px-2.5 py-1.5 bg-[#F7F8FA] border border-[#E4E7EC] rounded text-xs"
                required
              />
            </div>

            <button
              type="submit"
              disabled={createReportMutation.isPending}
              className="w-full py-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-bold text-xs rounded transition-colors"
            >
              {createReportMutation.isPending ? "Transmitting Signal..." : "Transmit Distress SOS Signal"}
            </button>
          </form>
        </div>

        {/* Operational Distress Queue Table (7 cols) */}
        <div className="lg:col-span-7 bg-white border border-[#E4E7EC] rounded-md overflow-hidden flex flex-col justify-between">
          <div className="p-3 border-b border-[#E4E7EC] bg-[#F7F8FA] flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#172033]">
              Active Distress Signals Queue ({reports.length})
            </h2>
            <span className="text-[10px] text-[#667085] font-mono">POLLING: 15s</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-[#E4E7EC] text-[10px] uppercase font-bold text-[#667085]">
                  <th className="py-2 px-3">Time</th>
                  <th className="py-2 px-3">Reporter</th>
                  <th className="py-2 px-3">Emergency Type</th>
                  <th className="py-2 px-3">Address</th>
                  <th className="py-2 px-3">Verification</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E4E7EC]">
                {isLoading ? (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-[#667085]">Loading distress queue...</td>
                  </tr>
                ) : reports.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-[#667085]">No active distress reports in queue.</td>
                  </tr>
                ) : (
                  reports.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50">
                      <td className="py-2 px-3 font-mono text-[11px] text-[#667085]">
                        {new Date(r.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="py-2 px-3 font-semibold text-[#172033]">{r.reporter_name}</td>
                      <td className="py-2 px-3 text-[#172033] font-medium">{r.disaster_type}</td>
                      <td className="py-2 px-3 text-[#667085] max-w-[160px] truncate">{r.address}</td>
                      <td className="py-2 px-3">
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                          r.is_verified
                            ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                            : "bg-amber-50 text-amber-800 border border-amber-200"
                        }`}>
                          {r.is_verified ? "VERIFIED" : "UNVERIFIED"}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>

    </div>
  );
};
