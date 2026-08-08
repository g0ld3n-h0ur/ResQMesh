import React from "react";
import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  TrendingUp,
  Package,
  Home,
  HeartPulse,
  FileText,
  Gauge,
  Link2,
  Settings,
  X,
  Radio,
  MapPin,
  CheckCircle,
  ShieldCheck,
  Building,
  BarChart3,
  LogOut,
  Shield
} from "lucide-react";
import { useAuthStore } from "../lib/authStore";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const location = useLocation();
  const { user, logout } = useAuthStore();

  const primaryMenuItems = [
    { name: "Command Center", path: "/", icon: LayoutDashboard, roles: ["government", "ngo", "hospital", "volunteer", "citizen"] },
    { name: "Citizen SOS", path: "/sos", icon: Radio, roles: ["citizen", "government", "ngo", "volunteer"] },
    { name: "AI Decisions", path: "/prediction", icon: TrendingUp, roles: ["government", "ngo"] },
    { name: "Resources", path: "/resources", icon: Package, roles: ["government", "ngo"] },
    { name: "Shelters", path: "/shelters", icon: Home, roles: ["government", "ngo", "hospital", "volunteer", "citizen"] },
    { name: "Hospitals", path: "/hospitals", icon: HeartPulse, roles: ["hospital", "government", "ngo"] },
    { name: "Priority Queue", path: "/priority", icon: Gauge, roles: ["government", "ngo"] },
    { name: "Coordination", path: "/coordination", icon: Link2, roles: ["government", "ngo", "volunteer"] },
    { name: "Routing & Maps", path: "/routing", icon: MapPin, roles: ["government", "ngo", "volunteer"] },
    { name: "Deliveries", path: "/proof-of-delivery", icon: CheckCircle, roles: ["government", "ngo", "volunteer"] },
    { name: "Audit Trail", path: "/audit", icon: ShieldCheck, roles: ["government", "ngo"] },
    { name: "CSR Tracking", path: "/csr", icon: Building, roles: ["government", "ngo", "citizen"] },
    { name: "Analytics", path: "/analytics", icon: BarChart3, roles: ["government", "ngo"] },
  ];

  const secondaryMenuItems = [
    { name: "Situation Reports", path: "/reports", icon: FileText, roles: ["government", "ngo", "hospital", "volunteer", "citizen"] },
    { name: "Settings", path: "/settings", icon: Settings, roles: ["government", "ngo", "hospital", "volunteer", "citizen"] },
  ];

  const currentRole = user?.role || "government";
  const filteredPrimary = primaryMenuItems.filter(item => item.roles.includes(currentRole));
  const filteredSecondary = secondaryMenuItems.filter(item => item.roles.includes(currentRole));

  return (
    <>
      {/* Mobile Sidebar Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/60 lg:hidden transition-opacity duration-200"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <aside 
        className={`fixed top-0 bottom-0 left-0 z-50 flex flex-col w-60 bg-slate-900 border-r border-slate-800 text-slate-300 transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:z-auto ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Header Branding */}
        <div className="flex items-center justify-between h-14 px-4 border-b border-slate-800 bg-slate-950">
          <div className="flex items-center space-x-2.5">
            <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-xs">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="font-extrabold text-sm text-white tracking-tight leading-none">ResQMesh</span>
              <span className="text-[9px] text-slate-400 font-semibold tracking-wider uppercase mt-0.5">Emergency Command</span>
            </div>
          </div>
          
          <button 
            className="p-1 rounded-md hover:bg-slate-800 lg:hidden"
            onClick={onClose}
          >
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>

        {/* User Role Card */}
        {user && (
          <div className="mx-3 mt-3 p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 flex items-center space-x-2.5">
            <div className="w-7 h-7 rounded-full bg-slate-800 text-slate-200 flex items-center justify-center font-bold text-xs shrink-0 border border-slate-700">
              {user.full_name?.charAt(0) || "U"}
            </div>
            <div className="overflow-hidden flex-1">
              <div className="text-xs font-semibold text-slate-200 truncate leading-tight">{user.full_name}</div>
              <span className="text-[9px] font-bold uppercase tracking-wider text-indigo-400">
                {user.role}
              </span>
            </div>
          </div>
        )}

        {/* Navigation Links */}
        <nav className="flex-1 py-3 px-3 space-y-0.5 overflow-y-auto">
          <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500 px-3 py-1">
            Operations
          </div>
          {filteredPrimary.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Link
                key={item.name}
                to={item.path}
                onClick={onClose}
                className={`flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                  isActive 
                    ? "bg-slate-800 text-white border border-slate-700 shadow-2xs font-bold" 
                    : "hover:bg-slate-800/60 hover:text-white text-slate-400"
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? "text-indigo-400" : "text-slate-400"}`} />
                <span className="truncate">{item.name}</span>
              </Link>
            );
          })}

          <div className="pt-3 text-[10px] uppercase font-bold tracking-wider text-slate-500 px-3 py-1">
            System
          </div>
          {filteredSecondary.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Link
                key={item.name}
                to={item.path}
                onClick={onClose}
                className={`flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                  isActive 
                    ? "bg-slate-800 text-white border border-slate-700 shadow-2xs font-bold" 
                    : "hover:bg-slate-800/60 hover:text-white text-slate-400"
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? "text-indigo-400" : "text-slate-400"}`} />
                <span className="truncate">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer Logout info */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <span className="text-[10px] text-slate-500 font-medium">
            ResQMesh v1.0
          </span>
          <button
            onClick={logout}
            className="p-1 rounded-md text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
            title="Log Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </aside>
    </>
  );
};
