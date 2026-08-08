import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Menu, Bell, LogOut, Clock, X } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "../lib/authStore";
import { api, unwrapList } from "../lib/api";

interface NavbarProps {
  onMenuToggle: () => void;
}

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  priority: string;
  is_read?: boolean;
  created_at: string;
}

export const Navbar: React.FC<NavbarProps> = ({ onMenuToggle }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAuthenticated } = useAuthStore();
  const queryClient = useQueryClient();
  const [showNotifications, setShowNotifications] = useState(false);

  // Fetch real notifications from backend /notifications endpoint
  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => {
      if (!isAuthenticated) return [];
      const res = await api.get("/notifications");
      return unwrapList<NotificationItem>(res);
    },
    enabled: isAuthenticated,
    refetchInterval: 15_000,
  });

  const unreadCount = notifications.filter(n => !n.is_read).length;

  const markReadMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.patch(`/notifications/${id}/read`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const getPageTitle = () => {
    switch (location.pathname) {
      case "/":
        return "Command Center Dashboard";
      case "/sos":
        return "Citizen Emergency SOS Interface";
      case "/prediction":
        return "AI Risk & Flood Priority Model";
      case "/resources":
        return "Resource Inventory & Allocation";
      case "/shelters":
        return "Emergency Shelter Coordinator";
      case "/hospitals":
        return "Hospital Fleet & Capacity";
      case "/priority":
        return "Priority Incident Ranking";
      case "/coordination":
        return "Multi-Agency Volunteer Coordination";
      case "/routing":
        return "Dynamic Rerouting Map Simulator";
      case "/proof-of-delivery":
        return "Proof of Delivery Verification";
      case "/audit":
        return "Audit Trail & Anomaly Alerts";
      case "/csr":
        return "CSR Tracking & Donor Transparency";
      case "/analytics":
        return "SLA Analytics & After-Action Review";
      case "/reports":
        return "Incident Situation Reports";
      case "/settings":
        return "Portal Configuration";
      default:
        return "ResQMesh Disaster Operations Platform";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority?.toUpperCase()) {
      case "CRITICAL":
      case "HIGH":
        return "text-rose-600 bg-rose-50 border-rose-200";
      case "MEDIUM":
      case "WARNING":
        return "text-amber-600 bg-amber-50 border-amber-200";
      default:
        return "text-indigo-600 bg-indigo-50 border-indigo-200";
    }
  };

  return (
    <header className="flex items-center justify-between h-16 px-6 bg-white border-b border-slate-200 shadow-sm z-30 relative">
      <div className="flex items-center space-x-4">
        <button
          className="p-2 rounded-lg hover:bg-slate-100 lg:hidden focus:outline-none text-slate-600"
          onClick={onMenuToggle}
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-lg font-bold text-slate-800 tracking-tight leading-tight">
            {getPageTitle()}
          </h1>
          <p className="text-[11px] text-slate-400 font-medium hidden sm:block">
            State Disaster Management Authority Telemetry
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-3 sm:space-x-4">
        {/* Notifications Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(prev => !prev)}
            className="relative p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-colors duration-150"
            title="Notifications & Alerts"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 bg-rose-600 text-white font-bold text-[10px] rounded-full flex items-center justify-center border-2 border-white">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>

          {/* Notifications Drawer Popover */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white border border-slate-200 rounded-2xl shadow-2xl z-50 overflow-hidden">
              <div className="p-3 bg-slate-900 text-white flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Bell className="w-4 h-4 text-indigo-400" />
                  <span className="text-xs font-bold uppercase tracking-wider">Live System Alerts</span>
                </div>
                <button
                  onClick={() => setShowNotifications(false)}
                  className="text-slate-400 hover:text-white p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                {notifications.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-400">
                    No active notifications available.
                  </div>
                ) : (
                  notifications.map((item) => (
                    <div
                      key={item.id}
                      className={`p-3.5 hover:bg-slate-50 transition-colors text-xs space-y-1 ${
                        !item.is_read ? "bg-indigo-50/30" : ""
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${getPriorityColor(item.priority)}`}>
                          {item.priority || "INFO"}
                        </span>
                        <span className="text-[10px] text-slate-400 flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>{new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </span>
                      </div>
                      <h4 className="font-semibold text-slate-800 text-xs mt-1">{item.title}</h4>
                      <p className="text-slate-500 text-[11px] leading-relaxed">{item.message}</p>
                      {!item.is_read && (
                        <button
                          onClick={() => markReadMutation.mutate(item.id)}
                          className="text-[10px] font-semibold text-indigo-600 hover:text-indigo-800 pt-1 block"
                        >
                          Mark as read
                        </button>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        <div className="h-6 w-px bg-slate-200" />

        {/* User Profile Summary */}
        <div className="flex items-center space-x-3">
          <div className="flex flex-col text-right hidden sm:flex">
            <span className="text-xs font-bold text-slate-800 truncate max-w-[140px]">
              {user?.full_name || "Authorized User"}
            </span>
            <span className="text-[10px] font-semibold uppercase text-indigo-600 tracking-wider">
              {user?.role || "Government"}
            </span>
          </div>

          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-700 text-white font-bold flex items-center justify-center shadow-sm">
            {user?.full_name?.charAt(0) || "U"}
          </div>

          <button
            onClick={() => {
              logout();
              navigate("/login");
            }}
            className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors"
            title="Log Out"
          >
            <LogOut className="w-4.5 h-4.5" />
          </button>
        </div>
      </div>
    </header>
  );
};
