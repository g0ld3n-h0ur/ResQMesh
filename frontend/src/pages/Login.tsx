import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  ShieldAlert,
  Building2,
  Users,
  HeartPulse,
  UserCheck,
  User,
  LogIn,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  UserPlus
} from "lucide-react";
import { useAuthStore, type UserRole } from "../lib/authStore";
import { api, formatApiError } from "../lib/api";

const PRESET_ACCOUNTS: Array<{
  role: UserRole;
  title: string;
  email: string;
  desc: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}> = [
  {
    role: "government",
    title: "Government Authority",
    email: "gov.admin@tn.gov.in",
    desc: "Full command center, AI prediction, & priority override",
    icon: Building2,
    color: "from-blue-600 to-indigo-700",
  },
  {
    role: "ngo",
    title: "NGO Coordinator",
    email: "ngo.lead@disasteraid.org",
    desc: "Resource allocation, volunteer ops, & CSR management",
    icon: Users,
    color: "from-emerald-600 to-teal-700",
  },
  {
    role: "hospital",
    title: "Hospital Operations",
    email: "hospital.admin@apollo.in",
    desc: "ICU & bed availability, emergency intake updates",
    icon: HeartPulse,
    color: "from-rose-600 to-red-700",
  },
  {
    role: "volunteer",
    title: "Field Volunteer",
    email: "volunteer.john@resqmesh.org",
    desc: "Task assignments, delivery verification & SOS response",
    icon: UserCheck,
    color: "from-purple-600 to-violet-700",
  },
  {
    role: "citizen",
    title: "Citizen",
    email: "citizen.priya@gmail.com",
    desc: "Emergency SOS distress signal & request status tracking",
    icon: User,
    color: "from-amber-600 to-orange-700",
  },
];

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading, error: authError } = useAuthStore();

  const [selectedRole, setSelectedRole] = useState<UserRole>("government");
  const [email, setEmail] = useState("gov.admin@tn.gov.in");
  const [password, setPassword] = useState("ResQMesh@2024!");
  const [localError, setLocalError] = useState<string | null>(null);

  // Registration modal state
  const [showRegister, setShowRegister] = useState(false);
  const [regFullName, setRegFullName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPhone, setRegPhone] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regOrg, setRegOrg] = useState("");
  const [regRole, setRegRole] = useState<UserRole>("citizen");
  const [regSuccess, setRegSuccess] = useState<string | null>(null);
  const [regError, setRegError] = useState<string | null>(null);
  const [regLoading, setRegLoading] = useState(false);

  const handlePresetSelect = (preset: typeof PRESET_ACCOUNTS[0]) => {
    setSelectedRole(preset.role);
    setEmail(preset.email);
    setPassword("ResQMesh@2024!");
    setLocalError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    if (!email || !password) {
      setLocalError("Please enter both email and password.");
      return;
    }

    const success = await login(email, password);
    if (success) {
      // Redirect to homepage or specific role dashboard
      if (selectedRole === "citizen") {
        navigate("/sos");
      } else {
        navigate("/");
      }
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegError(null);
    setRegSuccess(null);
    setRegLoading(true);

    try {
      const endpoint = `/auth/register/${regRole}`;
      const payload: Record<string, string> = {
        full_name: regFullName,
        email: regEmail,
        password: regPassword,
      };

      if (regPhone) payload.phone = regPhone;
      if (regRole !== "citizen" && regOrg) {
        payload.organization_name = regOrg;
      }

      const res = await api.post(endpoint, payload);
      if (res.data?.success) {
        setRegSuccess(`Account registered successfully as ${regRole.toUpperCase()}! You can now log in.`);
        setEmail(regEmail);
        setPassword(regPassword);
        setSelectedRole(regRole);
        setTimeout(() => {
          setShowRegister(false);
          setRegSuccess(null);
        }, 2000);
      }
    } catch (err: unknown) {
      setRegError(formatApiError(err, "Registration failed. Check inputs. Password requires 8+ chars with uppercase, lowercase, digit & symbol."));
    } finally {
      setRegLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 left-1/4 w-80 h-80 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header Branding */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center z-10">
        <div className="inline-flex items-center justify-center space-x-3 bg-slate-900 border border-slate-800 px-4 py-2 rounded-2xl shadow-xl mb-4">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white font-black shadow-lg shadow-indigo-500/20">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <span className="text-xl font-black text-white tracking-wide">
            ResQ<span className="text-indigo-400">Mesh</span>
          </span>
          <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
            v1.0
          </span>
        </div>
        <h2 className="text-2xl font-bold text-slate-100 tracking-tight">
          Disaster Command Operations Center
        </h2>
        <p className="mt-1 text-xs text-slate-400">
          Sign in to access AI prioritization, routing, and emergency coordination.
        </p>
      </div>

      {/* Main Container */}
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-4xl z-10 px-4">
        <div className="bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden grid md:grid-cols-12">
          
          {/* Left Panel: Role Selector Presets */}
          <div className="md:col-span-5 bg-slate-950/60 p-6 border-b md:border-b-0 md:border-r border-slate-800 flex flex-col justify-between">
            <div>
              <h3 className="text-xs uppercase font-bold tracking-wider text-slate-400 mb-3">
                Select Persona / Role
              </h3>
              <div className="space-y-2.5">
                {PRESET_ACCOUNTS.map((preset) => {
                  const Icon = preset.icon;
                  const isSelected = selectedRole === preset.role;
                  return (
                    <button
                      key={preset.role}
                      type="button"
                      onClick={() => handlePresetSelect(preset)}
                      className={`w-full text-left p-3 rounded-xl transition-all duration-200 flex items-center space-x-3 border ${
                        isSelected
                          ? "bg-slate-800/90 border-indigo-500/60 text-white shadow-lg ring-1 ring-indigo-500/40"
                          : "bg-slate-900/40 border-slate-800 text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                      }`}
                    >
                      <div
                        className={`w-8 h-8 rounded-lg flex items-center justify-center text-white bg-gradient-to-br ${preset.color} shrink-0`}
                      >
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="overflow-hidden">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-slate-200 truncate">
                            {preset.title}
                          </span>
                          {isSelected && (
                            <span className="w-2 h-2 rounded-full bg-indigo-400 shrink-0" />
                          )}
                        </div>
                        <p className="text-[10px] text-slate-400 truncate mt-0.5">
                          {preset.desc}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800/80 text-[11px] text-slate-400">
              <p className="flex items-center space-x-1">
                <span>Need a custom organization account?</span>
              </p>
              <button
                type="button"
                onClick={() => setShowRegister(true)}
                className="mt-1 text-indigo-400 hover:text-indigo-300 font-semibold inline-flex items-center space-x-1 transition-colors"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>Register new account</span>
              </button>
            </div>
          </div>

          {/* Right Panel: Login Credentials Form */}
          <div className="md:col-span-7 p-6 md:p-8 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-bold text-slate-100">
                    Sign In
                  </h3>
                  <p className="text-xs text-slate-400">
                    Authenticating as <span className="text-indigo-400 font-semibold capitalize">{selectedRole}</span>
                  </p>
                </div>
                <span className="text-[10px] px-2.5 py-1 rounded-full font-mono bg-slate-800 text-slate-300 border border-slate-700">
                  OAuth2 JWT
                </span>
              </div>

              {(localError || authError) && (
                <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-start space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{localError || authError}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-colors"
                    placeholder="user@organization.gov.in"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-colors"
                    placeholder="••••••••••••"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full mt-2 py-3 px-4 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-indigo-600/25 flex items-center justify-center space-x-2 transition-all duration-150 disabled:opacity-50"
                >
                  {isLoading ? (
                    <span>Authenticating with Backend...</span>
                  ) : (
                    <>
                      <LogIn className="w-4 h-4" />
                      <span>Authenticate & Launch Portal</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800 text-center">
              <p className="text-[11px] text-slate-400">
                Connected to FastAPI backend endpoint <code className="text-slate-300">/api/v1/auth/login</code>
              </p>
            </div>
          </div>

        </div>
      </div>

      {/* Registration Modal */}
      <AnimatePresence>
        {showRegister && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-slate-900 border border-slate-800 w-full max-w-lg rounded-3xl shadow-2xl p-6 relative overflow-hidden"
            >
              <h3 className="text-lg font-bold text-slate-100 mb-1">
                Register New User Account
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                Calls official backend endpoint <code className="text-indigo-400">/auth/register/{regRole}</code>
              </p>

              {regSuccess && (
                <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-300 text-xs flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{regSuccess}</span>
                </div>
              )}

              {regError && (
                <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-start space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{regError}</span>
                </div>
              )}

              <form onSubmit={handleRegisterSubmit} className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Role Type</label>
                  <select
                    value={regRole}
                    onChange={(e) => setRegRole(e.target.value as UserRole)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                  >
                    <option value="citizen">Citizen</option>
                    <option value="government">Government Authority</option>
                    <option value="ngo">NGO Coordinator</option>
                    <option value="hospital">Hospital Staff</option>
                    <option value="volunteer">Volunteer</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Full Name</label>
                    <input
                      type="text"
                      value={regFullName}
                      onChange={(e) => setRegFullName(e.target.value)}
                      required
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                      placeholder="Dr. Rajesh Kumar"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Phone Number</label>
                    <input
                      type="tel"
                      value={regPhone}
                      onChange={(e) => setRegPhone(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                      placeholder="+91 9876543210"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
                  <input
                    type="email"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    required
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                    placeholder="name@agency.org"
                  />
                </div>

                {regRole !== "citizen" && (
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Organization / Agency Name</label>
                    <input
                      type="text"
                      value={regOrg}
                      onChange={(e) => setRegOrg(e.target.value)}
                      required
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                      placeholder="Tamil Nadu State Disaster Relief"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
                  <input
                    type="password"
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                    required
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                    placeholder="Min 8 chars, 1 upper, 1 number, 1 symbol"
                  />
                </div>

                <div className="flex items-center justify-end space-x-3 pt-3">
                  <button
                    type="button"
                    onClick={() => setShowRegister(false)}
                    className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={regLoading}
                    className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/20 disabled:opacity-50"
                  >
                    {regLoading ? "Registering..." : "Submit Registration"}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
