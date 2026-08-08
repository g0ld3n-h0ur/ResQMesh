import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Shield,
  Building2,
  Users,
  HeartPulse,
  UserCheck,
  User,
  Check,
  ArrowRight,
  AlertCircle
} from "lucide-react";
import { useAuthStore, type UserRole } from "../lib/authStore";

interface RoleOption {
  role: UserRole;
  title: string;
  email: string;
  icon: React.ComponentType<{ className?: string }>;
  accentColor: string;
  badgeColor: string;
  capabilities: string[];
}

const ROLES: RoleOption[] = [
  {
    role: "government",
    title: "Government Authority",
    email: "gov.admin@tn.gov.in",
    icon: Building2,
    accentColor: "border-blue-600 text-blue-700 bg-blue-50/40",
    badgeColor: "bg-blue-600 text-white",
    capabilities: [
      "State Command Unit",
      "Emergency Declarations",
      "Clearance & Oversight"
    ]
  },
  {
    role: "ngo",
    title: "NGO Coordinator",
    email: "ngo.lead@disasteraid.org",
    icon: Users,
    accentColor: "border-emerald-600 text-emerald-700 bg-emerald-50/40",
    badgeColor: "bg-emerald-600 text-white",
    capabilities: [
      "Relief Logistics",
      "Field Units",
      "CSR Allocations"
    ]
  },
  {
    role: "hospital",
    title: "Hospital Operations",
    email: "hospital.admin@apollo.in",
    icon: HeartPulse,
    accentColor: "border-red-600 text-red-700 bg-red-50/40",
    badgeColor: "bg-red-600 text-white",
    capabilities: [
      "ICU & Bed Tracking",
      "Emergency Intake",
      "Trauma Units"
    ]
  },
  {
    role: "volunteer",
    title: "Field Volunteer",
    email: "volunteer.john@resqmesh.org",
    icon: UserCheck,
    accentColor: "border-purple-600 text-purple-700 bg-purple-50/40",
    badgeColor: "bg-purple-600 text-white",
    capabilities: [
      "Task Dispatch",
      "Incident Sign-Off",
      "Supply Verification"
    ]
  },
  {
    role: "citizen",
    title: "Citizen",
    email: "citizen.priya@gmail.com",
    icon: User,
    accentColor: "border-amber-600 text-amber-700 bg-amber-50/40",
    badgeColor: "bg-amber-600 text-white",
    capabilities: [
      "Emergency SOS Beacon",
      "Geolocation Tracking",
      "Response Status"
    ]
  }
];

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading, error: authError } = useAuthStore();
  const [selectedRole, setSelectedRole] = useState<UserRole>("government");
  const [localError, setLocalError] = useState<string | null>(null);

  const activeRoleObj = ROLES.find((r) => r.role === selectedRole) || ROLES[0];

  const handleContinue = async () => {
    setLocalError(null);
    const success = await login(activeRoleObj.email, "ResQMesh@2024!");
    if (success) {
      if (selectedRole === "citizen") {
        navigate("/sos");
      } else {
        navigate("/");
      }
    }
  };

  return (
    <div className="min-h-screen bg-[#F7FAFC] flex flex-col justify-between p-4 sm:p-6 lg:p-8 font-sans text-[#14213D] relative overflow-hidden">
      
      {/* Subtle Ambient Background Grid Pattern */}
      <div 
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(#14213D 1px, transparent 1px)`,
          backgroundSize: '24px 24px'
        }}
      />

      {/* Top Bar: System Status Panel */}
      <div className="relative z-10 flex items-center justify-between max-w-7xl mx-auto w-full">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-[#2563EB] text-white flex items-center justify-center font-bold shadow-xs">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <span className="font-extrabold text-lg text-[#14213D] tracking-tight">ResQMesh</span>
        </div>

        {/* System Status Panel */}
        <div className="flex items-center space-x-2.5 bg-white border border-[#E2E8F0] px-3.5 py-1.5 rounded-full shadow-2xs">
          <span className="w-2 h-2 rounded-full bg-[#16A34A] animate-pulse" />
          <div className="text-left leading-tight">
            <div className="text-[10px] uppercase font-bold tracking-wider text-[#16A34A]">
              SYSTEM OPERATIONAL
            </div>
            <div className="text-[10px] text-[#64748B]">All systems normal</div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="relative z-10 max-w-7xl mx-auto w-full my-auto py-8 space-y-8 text-center">
        
        {/* Branding Header */}
        <div className="space-y-2">
          <div className="inline-block px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-[#2563EB] text-xs font-extrabold uppercase tracking-widest">
            EMERGENCY OPERATIONS PLATFORM
          </div>

          <h1 className="text-3xl sm:text-4xl font-black text-[#14213D] tracking-tight">
            Access the Command Center
          </h1>

          <p className="text-base text-[#64748B] font-medium max-w-md mx-auto">
            Select your operating role to continue
          </p>

          {/* Accent Line */}
          <div className="w-12 h-1 bg-[#2563EB] mx-auto rounded-full mt-3" />
        </div>

        {(localError || authError) && (
          <div className="max-w-md mx-auto p-3 bg-red-50 border border-red-200 rounded-xl text-red-800 text-xs flex items-center justify-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
            <span>{localError || authError}</span>
          </div>
        )}

        {/* Role Selection Grid (5 Large Horizontal Cards on Desktop) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 text-left">
          {ROLES.map((roleObj) => {
            const Icon = roleObj.icon;
            const isSelected = selectedRole === roleObj.role;

            return (
              <div
                key={roleObj.role}
                onClick={() => setSelectedRole(roleObj.role)}
                className={`relative bg-white p-5 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between space-y-4 group ${
                  isSelected
                    ? "border-2 border-[#2563EB] shadow-md ring-2 ring-[#2563EB]/10 translate-y-[-2px]"
                    : "border-[#E2E8F0] shadow-2xs hover:border-slate-300 hover:shadow-xs"
                }`}
              >
                {/* Selected Check Indicator */}
                {isSelected && (
                  <div className="absolute top-3.5 right-3.5 w-5 h-5 rounded-full bg-[#2563EB] text-white flex items-center justify-center shadow-xs">
                    <Check className="w-3.5 h-3.5 stroke-[3]" />
                  </div>
                )}

                {/* Card Header & Icon */}
                <div className="space-y-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors ${
                    isSelected ? roleObj.badgeColor : "bg-slate-100 text-[#64748B] group-hover:bg-slate-200"
                  }`}>
                    <Icon className="w-5 h-5" />
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-[#14213D] leading-snug">
                      {roleObj.title}
                    </h3>
                  </div>
                </div>

                {/* Capability Bullet Points */}
                <ul className="space-y-1.5 pt-2 border-t border-[#E2E8F0]/80 text-xs text-[#64748B]">
                  {roleObj.capabilities.map((cap, idx) => (
                    <li key={idx} className="flex items-center space-x-1.5">
                      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${isSelected ? "bg-[#2563EB]" : "bg-slate-300"}`} />
                      <span className="font-medium">{cap}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>

        {/* Primary Action Button */}
        <div className="pt-4 flex flex-col items-center justify-center space-y-3">
          <button
            type="button"
            disabled={isLoading}
            onClick={handleContinue}
            className="w-full sm:w-auto min-w-[320px] py-3.5 px-8 bg-[#2563EB] hover:bg-blue-700 disabled:opacity-50 text-white font-bold text-sm rounded-xl shadow-md shadow-blue-600/15 flex items-center justify-center space-x-2.5 transition-all transform active:scale-[0.99]"
          >
            {isLoading ? (
              <span>Authenticating Session...</span>
            ) : (
              <>
                <span>Continue as {activeRoleObj.title}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>

          <span className="text-xs text-[#64748B] font-medium">
            Demo mode active • Direct single-click access
          </span>
        </div>

      </div>

      {/* Footer Branding */}
      <div className="relative z-10 max-w-7xl mx-auto w-full pt-6 border-t border-[#E2E8F0] flex flex-col sm:flex-row items-center justify-between gap-2 text-center sm:text-left">
        <div className="text-xs font-semibold text-[#64748B] uppercase tracking-wider">
          Secure • Reliable • Real-time
        </div>

        <div className="text-xs text-[#64748B]">
          © ResQMesh Operations Platform • State Emergency Response Network • v1.0
        </div>
      </div>

    </div>
  );
};
