import React, { useState } from "react";
import { 
  Settings as SettingsIcon, 
  User, 
  Building, 
  ShieldAlert, 
  CheckCircle2
} from "lucide-react";

export const Settings: React.FC = () => {
  const [formData, setFormData] = useState({
    name: "Arjun Krishnamurthy",
    email: "gov.admin@tn.gov.in",
    phone: "+919876543210",
    org: "Tamil Nadu Disaster Management Authority",
    district: "Chennai",
    state: "Tamil Nadu"
  });

  const [smsAlerts, setSmsAlerts] = useState(true);
  const [autoDispatch, setAutoDispatch] = useState(true);
  const [success, setSuccess] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSuccess(true);
    setTimeout(() => setSuccess(false), 3000);
  };

  return (
    <div className="max-w-3xl bg-white border border-slate-200 rounded-2xl shadow-sm p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3 pb-4 border-b border-slate-100">
        <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-100 text-slate-600 flex items-center justify-center">
          <SettingsIcon className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-slate-800">EOC Portal Configurations</h2>
          <p className="text-xs text-slate-400">Configure organization variables, profile metadata, and dispatch toggles.</p>
        </div>
      </div>

      {success && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold rounded-xl flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Profile configuration saved successfully!</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Profile details */}
        <div className="space-y-4">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1">
            <User className="w-3.5 h-3.5" />
            <span>Administrator Identity</span>
          </h3>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Full Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-xs font-medium"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Email Address</label>
              <input
                type="email"
                value={formData.email}
                className="w-full px-3 py-2 bg-slate-100 border border-slate-200 rounded-xl text-slate-500 text-xs font-medium cursor-not-allowed"
                disabled
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Mobile Phone</label>
              <input
                type="text"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-xs font-medium"
              />
            </div>
          </div>
        </div>

        {/* Organization details */}
        <div className="space-y-4 pt-4 border-t border-slate-100">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1">
            <Building className="w-3.5 h-3.5" />
            <span>Organization Parameters</span>
          </h3>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1 sm:col-span-2">
              <label className="text-xs font-semibold text-slate-700">Organization Title</label>
              <input
                type="text"
                value={formData.org}
                onChange={(e) => setFormData({ ...formData, org: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-xs font-medium"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">EOC District</label>
              <input
                type="text"
                value={formData.district}
                className="w-full px-3 py-2 bg-slate-100 border border-slate-200 rounded-xl text-slate-500 text-xs font-medium cursor-not-allowed"
                disabled
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">EOC State</label>
              <input
                type="text"
                value={formData.state}
                className="w-full px-3 py-2 bg-slate-100 border border-slate-200 rounded-xl text-slate-500 text-xs font-medium cursor-not-allowed"
                disabled
              />
            </div>
          </div>
        </div>

        {/* Dispatch Controls */}
        <div className="space-y-4 pt-4 border-t border-slate-100">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1">
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Crisis & Dispatch Toggles</span>
          </h3>

          <div className="space-y-3">
            {[
              {
                title: "SMS Broadcast Signals",
                desc: "Send critical EOC alerts to registered volunteer phones immediately.",
                state: smsAlerts,
                setter: setSmsAlerts
              },
              {
                title: "Auto-Volunteer Dispatch",
                desc: "Automatically suggest volunteer listings to nearby safe shelters during critical alerts.",
                state: autoDispatch,
                setter: setAutoDispatch
              }
            ].map((toggle, i) => (
              <div key={i} className="flex items-start justify-between p-3 bg-slate-50 rounded-xl border border-slate-100">
                <div className="space-y-0.5">
                  <span className="text-xs font-bold text-slate-700">{toggle.title}</span>
                  <p className="text-[10px] text-slate-400 font-medium leading-normal">{toggle.desc}</p>
                </div>
                <button
                  type="button"
                  onClick={() => toggle.setter(!toggle.state)}
                  className={`w-10 h-6 flex items-center rounded-full p-1 transition-colors duration-200 focus:outline-none ${
                    toggle.state ? "bg-indigo-600" : "bg-slate-300"
                  }`}
                >
                  <div
                    className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-200 ${
                      toggle.state ? "translate-x-4" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Form Submission */}
        <div className="pt-4 border-t border-slate-100 flex items-center justify-end">
          <button
            type="submit"
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-sm transition"
          >
            Save EOC Options
          </button>
        </div>
      </form>
    </div>
  );
};
