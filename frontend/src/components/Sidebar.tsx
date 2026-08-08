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
  LogOut
} from "lucide-react";
import { useAuthStore } from "../lib/authStore";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const location = useLocation();
  const { user, logout } = useAuthStore();

  const menuItems = [
    { name: "Command Center", path: "/", icon: LayoutDashboard, roles: ["government", "ngo", "hospital", "volunteer", "citizen"] },
    { name: "Citizen SOS", path: "/sos", icon: Radio, roles: ["citizen", "government", "ngo", "volunteer"] },
    { name: "AI Prediction & Action Plan", path: "/prediction", icon: TrendingUp, roles: ["government", "ngo"] },
    { name: "Resource Allocation", path: "/resources", icon: Package, roles: ["government", "ngo"] },
    { name: "Shelters", path: "/shelters", icon: Home, roles: ["government", "ngo", "hospital", "volunteer", "citizen"] },
    { name: "Hospitals", path: "/hospitals", icon: HeartPulse, roles: ["hospital", "government", "ngo"] },
    { name: "Priority Ranking", path: "/priority", icon: Gauge, roles: ["government", "ngo"] },
    { name: "Coordination & Volunteers", path: "/coordination", icon: Link2, roles: ["government", "ngo", "volunteer"] },
    { name: "Dynamic Rerouting Map", path: "/routing", icon: MapPin, roles: ["government", "ngo", "volunteer"] },
    { name: "Proof of Delivery", path: "/proof-of-delivery", icon: CheckCircle, roles: ["government", "ngo", "volunteer"] },
    { name: "Audit & Anomaly Alerts", path: "/audit", icon: ShieldCheck, roles: ["government", "ngo"] },
    { name: "CSR & Transparency", path: "/csr", icon: Building, roles: ["government", "ngo", "citizen"] },
    { name: "Analytics & Preparedness", path: "/analytics", icon: BarChart3, roles: ["government", "ngo"] },
    { name: "Situation Reports", path: "/reports", icon: FileText, roles: ["government", "ngo", "hospital", "volunteer", "citizen"] },
    { name: "Settings", path: "/settings", icon: Settings, roles: ["government", "ngo", "hospital", "volunteer", "citizen"] },
  ];

  const currentRole = user?.role || "government";
  const filteredItems = menuItems.filter(item => item.roles.includes(currentRole));

  return (
    <>
      {/* Mobile Sidebar Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs lg:hidden transition-opacity duration-300"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <aside 
        className={`fixed top-0 bottom-0 left-0 z-50 flex flex-col w-64 bg-slate-900 border-r border-slate-800 text-slate-300 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:z-auto ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Header Branding */}
        <div className="flex items-center justify-between h-16 px-5 border-b border-slate-800 bg-slate-950">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center font-black text-white shadow-md shadow-indigo-500/30">
              R
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-base text-white tracking-wide leading-tight">ResQMesh</span>
              <span className="text-[10px] text-indigo-400 font-medium tracking-widest uppercase">Command Platform</span>
            </div>
          </div>
          
          {/* Close button on mobile */}
          <button 
            className="p-1 rounded-md hover:bg-slate-800 lg:hidden"
            onClick={onClose}
          >
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        {/* User Role Card */}
        {user && (
          <div className="mx-3 mt-3 p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-xs shrink-0">
              {user.full_name?.charAt(0) || "U"}
            </div>
            <div className="overflow-hidden flex-1">
              <div className="text-xs font-semibold text-slate-200 truncate">{user.full_name}</div>
              <div className="flex items-center space-x-1 mt-0.5">
                <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {user.role}
                </span>
                {user.organization_name && (
                  <span className="text-[10px] text-slate-400 truncate">
                    • {user.organization_name}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Navigation Links */}
        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {filteredItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Link
                key={item.name}
                to={item.path}
                onClick={onClose}
                className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all duration-150 ${
                  isActive 
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20 font-semibold" 
                    : "hover:bg-slate-800/80 hover:text-white text-slate-400"
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? "text-white" : "text-slate-400 group-hover:text-white"}`} />
                <span className="truncate">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer Logout info */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div className="text-[10px] text-slate-500">
            ResQMesh Operations v1.0
          </div>
          <button
            onClick={logout}
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
            title="Sign out of portal"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </aside>
    </>
  );
};
