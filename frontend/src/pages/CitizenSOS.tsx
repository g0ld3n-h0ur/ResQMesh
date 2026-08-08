import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Radio,
  MapPin,
  AlertTriangle,
  Send,
  CheckCircle2,
  Phone,
  Flame,
  Waves,
  HeartPulse,
  Building,
  Shield
} from "lucide-react";
import { api, formatApiError } from "../lib/api";

const EMERGENCY_TYPES = [
  { id: "Flood", label: "Severe Flood / Inundation", icon: Waves, color: "from-blue-600 to-cyan-600" },
  { id: "Fire", label: "Wildfire / Structural Fire", icon: Flame, color: "from-amber-600 to-rose-600" },
  { id: "Medical Emergency", label: "Critical Medical Need", icon: HeartPulse, color: "from-rose-600 to-red-600" },
  { id: "Building Collapse", label: "Infrastructure Collapse / Trapped", icon: Building, color: "from-slate-700 to-slate-900" },
  { id: "Other", label: "General Disaster Rescue", icon: Shield, color: "from-indigo-600 to-purple-600" },
];

interface SOSReportResult {
  id: string;
  disaster_type: string;
  address: string;
  is_verified: boolean;
  created_at: string;
  description: string;
}

export const CitizenSOS: React.FC = () => {
  const [disasterType, setDisasterType] = useState("Flood");
  const [description, setDescription] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [location, setLocation] = useState<{ lat: number | null; lng: number | null }>({
    lat: null,
    lng: null,
  });
  const [locationStatus, setLocationStatus] = useState<string>("Not acquired");
  const [isLocating, setIsLocating] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submittedReport, setSubmittedReport] = useState<SOSReportResult | null>(null);

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus("Geolocation is not supported by your browser");
      return;
    }

    setIsLocating(true);
    setLocationStatus("Acquiring GPS coordinates...");

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
        setLocationStatus(`GPS Fixed: ${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`);
        if (!address) {
          setAddress(`GPS Lat: ${position.coords.latitude.toFixed(4)}, Lng: ${position.coords.longitude.toFixed(4)}`);
        }
        setIsLocating(false);
      },
      (err) => {
        console.warn("Geolocation error:", err);
        setLocationStatus(`GPS permission denied or unavailable: ${err.message}`);
        setIsLocating(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // POST /api/v1/reports endpoint
      const payload = {
        disaster_type: disasterType,
        description: description,
        phone: phone || "9999999999",
        address: address || "Emergency Location",
        latitude: location.lat,
        longitude: location.lng,
      };

      const res = await api.post("/reports", payload);
      if (res.data?.success) {
        setSubmittedReport(res.data.data);
      } else {
        setError(res.data?.message || "SOS distress signal failed to register.");
      }
    } catch (err: unknown) {
      setError(formatApiError(err, "Failed to send SOS signal. Check network connection."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-rose-950 via-slate-900 to-slate-900 border border-rose-900/40 rounded-3xl p-6 shadow-xl text-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-rose-600 flex items-center justify-center font-bold text-white shadow-lg shadow-rose-600/40 shrink-0 animate-pulse">
            <Radio className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-extrabold tracking-tight">Citizen Emergency SOS Beacon</h2>
              <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40">
                LIVE DISPATCH
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              Direct telemetry stream to State Command Center & nearby rescue squads.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 bg-slate-950/60 border border-slate-800 px-4 py-2 rounded-2xl">
          <Phone className="w-4 h-4 text-rose-400" />
          <div className="text-xs">
            <span className="text-slate-400 block text-[10px]">Toll-Free Helpline</span>
            <span className="font-mono font-bold text-slate-100">1070 / 112</span>
          </div>
        </div>
      </div>

      {/* Main SOS Flow */}
      {submittedReport ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white border border-emerald-200 rounded-3xl p-8 shadow-xl text-center space-y-6 max-w-2xl mx-auto"
        >
          <div className="w-16 h-16 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto ring-8 ring-emerald-50">
            <CheckCircle2 className="w-10 h-10" />
          </div>
          <div>
            <span className="text-xs uppercase font-bold tracking-widest px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
              DISPATCHED TO COMMAND CENTER
            </span>
            <h3 className="text-xl font-bold text-slate-800 mt-3">
              SOS Signal Received & Prioritized
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Incident Ref ID: <code className="font-mono font-bold text-slate-800">{submittedReport.id}</code>
            </p>
          </div>

          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-left text-xs space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-500">Emergency Type:</span>
              <span className="font-semibold text-slate-800">{submittedReport.disaster_type}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Verification Status:</span>
              <span className="font-semibold text-indigo-600">Pending Field Verification</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Location:</span>
              <span className="font-semibold text-slate-800 truncate max-w-[250px]">{submittedReport.address}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Timestamp:</span>
              <span className="font-mono text-slate-600">{new Date(submittedReport.created_at).toLocaleString()}</span>
            </div>
          </div>

          <button
            onClick={() => setSubmittedReport(null)}
            className="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-xl shadow-md"
          >
            Submit Another SOS Incident
          </button>
        </motion.div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* SOS Form */}
          <div className="lg:col-span-2 bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-base font-bold text-slate-800">Submit Emergency SOS Incident</h3>
                <p className="text-xs text-slate-400">Fill in details for immediate automated triage.</p>
              </div>
              <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-slate-100 text-slate-600 border border-slate-200">
                POST /api/v1/reports
              </span>
            </div>

            {error && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Type Selection */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">
                  1. Select Emergency Type
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {EMERGENCY_TYPES.map((type) => {
                    const Icon = type.icon;
                    const isSelected = disasterType === type.id;
                    return (
                      <button
                        key={type.id}
                        type="button"
                        onClick={() => setDisasterType(type.id)}
                        className={`p-3 rounded-2xl text-left border transition-all flex flex-col justify-between space-y-2 ${
                          isSelected
                            ? "bg-slate-900 border-indigo-600 text-white shadow-md ring-2 ring-indigo-500/20"
                            : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100"
                        }`}
                      >
                        <div className={`w-7 h-7 rounded-xl flex items-center justify-center text-white bg-gradient-to-tr ${type.color}`}>
                          <Icon className="w-4 h-4" />
                        </div>
                        <span className="text-xs font-semibold leading-tight">{type.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Location telemetry */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                    2. Location Telemetry
                  </label>
                  <button
                    type="button"
                    onClick={handleGetLocation}
                    disabled={isLocating}
                    className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold flex items-center space-x-1"
                  >
                    <MapPin className="w-3.5 h-3.5" />
                    <span>{isLocating ? "Locating..." : "Use Browser Geolocation"}</span>
                  </button>
                </div>

                <div className="space-y-2">
                  <input
                    type="text"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    required
                    placeholder="Enter landmark, district, or street address (e.g. Velachery main road near bridge)"
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500"
                  />
                  <div className="text-[11px] text-slate-400 font-mono bg-slate-100 px-3 py-1.5 rounded-lg flex items-center space-x-2">
                    <MapPin className="w-3 h-3 text-indigo-500" />
                    <span>{locationStatus}</span>
                  </div>
                </div>
              </div>

              {/* Description & Contact */}
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
                    3. Contact Phone Number
                  </label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    required
                    placeholder="+91 9876543210"
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/10"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
                    4. Incident Details & Trapped Count
                  </label>
                  <input
                    type="text"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    required
                    placeholder="e.g. Water level 5ft, 4 people trapped on rooftop"
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/10"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 bg-rose-600 hover:bg-rose-500 text-white text-sm font-extrabold rounded-2xl shadow-lg shadow-rose-600/30 flex items-center justify-center space-x-2 transition-all duration-150"
              >
                {loading ? (
                  <span>Transmitting SOS to Backend...</span>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    <span>TRANSMIT EMERGENCY DISTRESS SIGNAL</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Guidelines Sidebar */}
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 text-white space-y-4 shadow-sm">
              <div className="flex items-center space-x-2">
                <Shield className="w-5 h-5 text-indigo-400" />
                <h4 className="text-sm font-bold">ResQMesh Emergency Triage Protocol</h4>
              </div>
              <ul className="text-xs text-slate-300 space-y-2.5">
                <li className="flex items-start space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500 mt-1.5 shrink-0" />
                  <span>Distress reports are routed directly to the AI prioritization classifier.</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                  <span>High-priority medical and trapped reports trigger immediate volunteer notifications.</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                  <span>Stay on elevated ground if flood waters are rising.</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
