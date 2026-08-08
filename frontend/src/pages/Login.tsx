import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Shield,
  Building2,
  Users,
  HeartPulse,
  UserCheck,
  User,
  ArrowRight,
  AlertCircle,
  Lock
} from "lucide-react";
import { useAuthStore, type UserRole } from "../lib/authStore";

const ROLES: Array<{
  role: UserRole;
  title: string;
  subtitle: string;
  email: string;
  icon: React.ComponentType<{ className?: string }>;
  accent: string;
}> = [
  {
    role: "government",
    title: "Government Authority",
    subtitle: "State command center, resource clearance & emergency declarations",
    email: "gov.admin@tn.gov.in",
    icon: Building2,
    accent: "border-blue-600 bg-blue-50/50 text-blue-900",
  },
  {
    role: "ngo",
    title: "NGO Coordinator",
    subtitle: "Relief logistics, volunteer deployment & CSR allocations",
    email: "ngo.lead@disasteraid.org",
    icon: Users,
    accent: "border-emerald-600 bg-emerald-50/50 text-emerald-900",
  },
  {
    role: "hospital",
    title: "Hospital Operations",
    subtitle: "ICU bed tracking, emergency intake & medical capacity",
    email: "hospital.admin@apollo.in",
    icon: HeartPulse,
    accent: "border-rose-600 bg-rose-50/50 text-rose-900",
  },
  {
    role: "volunteer",
    title: "Field Volunteer",
    subtitle: "On-site dispatch, task sign-off & relief delivery verification",
    email: "volunteer.john@resqmesh.org",
    icon: UserCheck,
    accent: "border-purple-600 bg-purple-50/50 text-purple-900",
  },
  {
    role: "citizen",
    title: "Citizen",
    subtitle: "Submit emergency SOS distress signals & track response status",
    email: "citizen.priya@gmail.com",
    icon: User,
    accent: "border-amber-600 bg-amber-50/50 text-amber-900",
  },
];

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading, error: authError } = useAuthStore();

  const [selectedRole, setSelectedRole] = useState<UserRole>("government");
  const [email, setEmail] = useState("gov.admin@tn.gov.in");
  const [password, setPassword] = useState("ResQMesh@2024!");
  const [localError, setLocalError] = useState<string | null>(null);

  const handleRoleSelect = (role: typeof ROLES[0]) => {
    setSelectedRole(role.role);
    setEmail(role.email);
    setPassword("ResQMesh@2024!");
    setLocalError(null);
  };

  const handleEnterPortal = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    if (!email || !password) {
      setLocalError("Please enter valid credentials.");
      return;
    }

    const success = await login(email, password);
    if (success) {
      if (selectedRole === "citizen") {
        navigate("/sos");
      } else {
        navigate("/");
      }
    }
  };

  const activeRoleObj = ROLES.find((r) => r.role === selectedRole) || ROLES[0];

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-center py-10 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="max-w-4xl mx-auto w-full space-y-6">
        
        {/* Header Branding */}
        <div className="flex items-center justify-between bg-white border border-slate-200 p-5 rounded-2xl shadow-xs">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center font-extrabold text-base shadow-sm">
              <Shield className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-lg font-black text-slate-900 tracking-tight leading-tight">
                ResQMesh Emergency Operations Platform
              </h1>
              <p className="text-xs text-slate-500 font-medium">
                State Disaster Management Telemetry & Unified Command Portal
              </p>
            </div>
          </div>

          <div className="hidden sm:flex items-center space-x-2 text-xs text-slate-500 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg">
            <Lock className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-semibold">Secure Authorization</span>
          </div>
        </div>

        {/* Main Card Grid */}
        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden grid md:grid-cols-12">
          
          {/* Left Column: Role Selector */}
          <div className="md:col-span-6 p-6 border-b md:border-b-0 md:border-r border-slate-200 bg-slate-50/50 space-y-4">
            <div>
              <h2 className="text-xs uppercase font-bold tracking-wider text-slate-500">
                1. Select Operational Role
              </h2>
              <p className="text-xs text-slate-600 mt-0.5">
                Choose access profile for localized command dashboard features.
              </p>
            </div>

            <div className="space-y-2.5">
              {ROLES.map((roleObj) => {
                const Icon = roleObj.icon;
                const isSelected = selectedRole === roleObj.role;
                return (
                  <button
                    key={roleObj.role}
                    type="button"
                    onClick={() => handleRoleSelect(roleObj)}
                    className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-start space-x-3 ${
                      isSelected
                        ? `${roleObj.accent} shadow-xs font-semibold ring-1 ring-slate-400`
                        : "bg-white border-slate-200 text-slate-700 hover:bg-slate-100/80"
                    }`}
                  >
                    <div className={`p-2 rounded-lg shrink-0 ${isSelected ? "bg-white text-slate-900 shadow-2xs" : "bg-slate-100 text-slate-600"}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="overflow-hidden">
                      <div className="text-xs font-bold text-slate-900 leading-tight">
                        {roleObj.title}
                      </div>
                      <div className="text-[11px] text-slate-500 truncate mt-0.5">
                        {roleObj.subtitle}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Column: Portal Launcher */}
          <div className="md:col-span-6 p-6 md:p-8 flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div>
                <h2 className="text-xs uppercase font-bold tracking-wider text-slate-500">
                  2. Authorize Access
                </h2>
                <h3 className="text-base font-bold text-slate-900 mt-0.5">
                  Continue as {activeRoleObj.title}
                </h3>
              </div>

              {(localError || authError) && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-start space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
                  <span>{localError || authError}</span>
                </div>
              )}

              <form onSubmit={handleEnterPortal} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Official Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-800 font-medium"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Security Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-800 font-medium"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-3 px-4 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold uppercase tracking-wider rounded-xl shadow-sm flex items-center justify-center space-x-2 transition-all disabled:opacity-50"
                >
                  {isLoading ? (
                    <span>Verifying Access...</span>
                  ) : (
                    <>
                      <span>Enter Command Center as {activeRoleObj.title.split(" ")[0]}</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>
            </div>

            <div className="pt-4 border-t border-slate-100 text-center">
              <span className="text-[11px] text-slate-400 font-medium">
                State Disaster Operations Center Telemetry Network
              </span>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
