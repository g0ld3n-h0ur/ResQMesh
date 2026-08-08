import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore, type UserRole } from "../lib/authStore";

const ROLES: Array<{
  role: UserRole;
  title: string;
  subtitle: string;
  email: string;
}> = [
  {
    role: "government",
    title: "Government Authority",
    subtitle: "State Command Unit • Emergency Declarations • Clearance",
    email: "gov.admin@tn.gov.in",
  },
  {
    role: "ngo",
    title: "NGO Coordinator",
    subtitle: "Relief Logistics • Field Units • CSR Allocations",
    email: "ngo.lead@disasteraid.org",
  },
  {
    role: "hospital",
    title: "Hospital Operations",
    subtitle: "ICU & Bed Tracking • Emergency Intake • Trauma Units",
    email: "hospital.admin@apollo.in",
  },
  {
    role: "volunteer",
    title: "Field Volunteer",
    subtitle: "Task Dispatch • Incident Sign-Off • Supply Verification",
    email: "volunteer.john@resqmesh.org",
  },
  {
    role: "citizen",
    title: "Citizen",
    subtitle: "Emergency Distress SOS • Status Tracking",
    email: "citizen.priya@gmail.com",
  },
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
    <div className="min-h-screen bg-[#F7F8FA] flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white border border-[#E4E7EC] rounded-lg shadow-xs p-6 space-y-5">
        
        {/* Header */}
        <div className="border-b border-[#E4E7EC] pb-4">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-600" />
            <h1 className="text-base font-bold text-[#172033] tracking-tight">
              ResQMesh Operations
            </h1>
          </div>
          <p className="text-xs text-[#667085] mt-1 font-medium">
            Emergency Management Control Portal Access
          </p>
        </div>

        {/* Role Selection */}
        <div className="space-y-3">
          <label className="text-[11px] font-bold uppercase tracking-wider text-[#667085]">
            Select Operating Role:
          </label>

          <div className="space-y-1.5">
            {ROLES.map((r) => {
              const isSelected = selectedRole === r.role;
              return (
                <button
                  key={r.role}
                  type="button"
                  onClick={() => setSelectedRole(r.role)}
                  className={`w-full text-left p-3 rounded-md border text-xs transition-colors flex items-center justify-between ${
                    isSelected
                      ? "bg-slate-100 border-[#172033] font-bold text-[#172033]"
                      : "bg-white border-[#E4E7EC] text-[#172033] hover:bg-slate-50"
                  }`}
                >
                  <div>
                    <div className="font-semibold text-xs">{r.title}</div>
                    <div className="text-[10px] text-[#667085] font-normal mt-0.5">{r.subtitle}</div>
                  </div>
                  {isSelected && <span className="w-2 h-2 rounded-full bg-blue-600 shrink-0" />}
                </button>
              );
            })}
          </div>
        </div>

        {(localError || authError) && (
          <div className="p-2.5 bg-red-50 border border-red-200 text-red-700 text-xs rounded">
            {localError || authError}
          </div>
        )}

        {/* Primary Action Button */}
        <button
          type="button"
          disabled={isLoading}
          onClick={handleContinue}
          className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold text-xs rounded transition-colors"
        >
          {isLoading ? "Authenticating Session..." : `Continue as ${activeRoleObj.title}`}
        </button>

        <div className="text-center pt-1 border-t border-[#E4E7EC]">
          <span className="text-[10px] text-[#667085]">
            State Emergency Telemetry System • ResQMesh Operations v1.0
          </span>
        </div>
      </div>
    </div>
  );
};
