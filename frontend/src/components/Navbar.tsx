import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "../lib/authStore";
import { api, unwrapList } from "../lib/api";

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  priority: string;
  is_read: boolean;
  created_at: string;
}

interface NavbarProps {
  onToggleSidebar?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleSidebar }) => {
  const { user, logout } = useAuthStore();
  const queryClient = useQueryClient();
  const [showNotifications, setShowNotifications] = useState(false);

  const { data: notifications = [] } = useQuery<NotificationItem[]>({
    queryKey: ["navbar-notifications"],
    queryFn: async () => unwrapList<NotificationItem>(await api.get("/notifications/")),
    refetchInterval: 30_000,
  });

  const markAsReadMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.patch(`/notifications/${id}/read`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["navbar-notifications"] });
    },
  });

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <header className="h-12 bg-white border-b border-[#E4E7EC] px-4 flex items-center justify-between text-xs sticky top-0 z-30 font-sans">
      
      {/* Left Branding & Mobile Toggle */}
      <div className="flex items-center space-x-3">
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            className="p-1 rounded text-[#667085] hover:bg-slate-100 lg:hidden"
          >
            ☰
          </button>
        )}
        <div className="flex items-center space-x-2">
          <span className="font-bold text-[#172033] tracking-tight">ResQMesh</span>
          <span className="hidden sm:inline text-[#667085]">|</span>
          <span className="hidden sm:inline font-semibold text-[#172033]">
            Tamil Nadu Response Network
          </span>
        </div>
      </div>

      {/* Center Operational Status */}
      <div className="hidden md:flex items-center space-x-3 text-[11px]">
        <span className="flex items-center space-x-1.5 text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse" />
          <span>Operational</span>
        </span>
        <span className="text-[#667085]">Updated {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-3">
        {/* Notifications Button */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative px-2 py-1 text-[#667085] hover:text-[#172033] font-medium text-xs flex items-center space-x-1"
          >
            <span>Alerts</span>
            {unreadCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-red-600 text-white font-mono text-[9px] font-bold">
                {unreadCount}
              </span>
            )}
          </button>

          {/* Notifications Dropdown Drawer */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-72 bg-white border border-[#E4E7EC] shadow-sm rounded p-3 space-y-2 z-50">
              <div className="flex items-center justify-between border-b border-[#E4E7EC] pb-2">
                <span className="font-bold text-[#172033]">System Notifications</span>
                <span className="text-[10px] text-[#667085]">{unreadCount} unread</span>
              </div>
              <div className="divide-y divide-slate-100 max-h-60 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="py-3 text-center text-[#667085] text-[11px]">No alerts</div>
                ) : (
                  notifications.slice(0, 5).map((n) => (
                    <div key={n.id} className="py-2 text-[11px] space-y-0.5">
                      <div className="flex justify-between font-semibold text-[#172033]">
                        <span>{n.title}</span>
                        {!n.is_read && (
                          <button
                            onClick={() => markAsReadMutation.mutate(n.id)}
                            className="text-[9px] text-blue-600 underline hover:text-blue-800"
                          >
                            Dismiss
                          </button>
                        )}
                      </div>
                      <p className="text-[#667085] text-[10px] line-clamp-1">{n.message}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Profile */}
        {user ? (
          <div className="flex items-center space-x-2 border-l border-[#E4E7EC] pl-3">
            <span className="font-semibold text-[#172033] capitalize">{user.role}</span>
            <button
              onClick={logout}
              className="text-[11px] text-[#667085] hover:text-red-600 underline font-medium"
            >
              Logout
            </button>
          </div>
        ) : (
          <a href="/login" className="text-blue-600 font-semibold hover:underline">
            Login
          </a>
        )}
      </div>

    </header>
  );
};
