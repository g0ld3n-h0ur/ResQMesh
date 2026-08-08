import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuthStore } from "../lib/authStore";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const location = useLocation();
  const { user } = useAuthStore();

  const sections = [
    {
      title: "COMMAND",
      items: [
        { name: "Command Center", path: "/", roles: ["government", "ngo", "hospital", "volunteer", "citizen"] },
        { name: "Incidents Queue", path: "/sos", roles: ["citizen", "government", "ngo", "volunteer"] },
        { name: "Priority Queue", path: "/priority", roles: ["government", "ngo"] },
      ],
    },
    {
      title: "OPERATIONS",
      items: [
        { name: "Resources", path: "/resources", roles: ["government", "ngo"] },
        { name: "Shelters", path: "/shelters", roles: ["government", "ngo", "hospital", "volunteer", "citizen"] },
        { name: "Hospitals", path: "/hospitals", roles: ["hospital", "government", "ngo"] },
        { name: "Coordination", path: "/coordination", roles: ["government", "ngo", "volunteer"] },
        { name: "Routing", path: "/routing", roles: ["government", "ngo", "volunteer"] },
        { name: "Deliveries", path: "/proof-of-delivery", roles: ["government", "ngo", "volunteer"] },
      ],
    },
    {
      title: "ANALYSIS",
      items: [
        { name: "AI Decisions", path: "/prediction", roles: ["government", "ngo"] },
        { name: "Analytics", path: "/analytics", roles: ["government", "ngo"] },
        { name: "Audit Trail", path: "/audit", roles: ["government", "ngo"] },
        { name: "CSR Tracking", path: "/csr", roles: ["government", "ngo", "citizen"] },
      ],
    },
    {
      title: "OTHER",
      items: [
        { name: "Reports", path: "/reports", roles: ["government", "ngo", "hospital", "volunteer", "citizen"] },
        { name: "Settings", path: "/settings", roles: ["government", "ngo", "hospital", "volunteer", "citizen"] },
      ],
    },
  ];

  const currentRole = user?.role || "government";

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/30 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 flex flex-col w-56 bg-white border-r border-[#E4E7EC] text-[#172033] transform transition-transform duration-150 ease-in-out lg:translate-x-0 lg:static lg:z-auto ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Logo Header */}
        <div className="flex items-center justify-between h-12 px-4 border-b border-[#E4E7EC]">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-blue-600" />
            <span className="font-bold text-sm tracking-tight text-[#172033]">ResQMesh</span>
          </div>
          <span className="text-[10px] text-[#667085] font-mono uppercase">Ops</span>
        </div>

        {/* User Role Card */}
        {user && (
          <div className="px-3 py-2 bg-slate-50 border-b border-[#E4E7EC] flex items-center justify-between">
            <span className="text-xs font-semibold truncate text-[#172033]">{user.full_name}</span>
            <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-slate-200 text-slate-700">
              {user.role}
            </span>
          </div>
        )}

        {/* Navigation Section List */}
        <nav className="flex-1 py-2 px-2 space-y-3 overflow-y-auto">
          {sections.map((section) => {
            const filteredItems = section.items.filter((i) => i.roles.includes(currentRole));
            if (filteredItems.length === 0) return null;

            return (
              <div key={section.title} className="space-y-0.5">
                <div className="text-[10px] uppercase font-bold tracking-wider text-[#667085] px-2 py-0.5">
                  {section.title}
                </div>
                {filteredItems.map((item) => {
                  const isActive = location.pathname === item.path;
                  return (
                    <Link
                      key={item.name}
                      to={item.path}
                      onClick={onClose}
                      className={`block px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
                        isActive
                          ? "bg-slate-100 text-blue-700 font-semibold border-l-2 border-blue-600"
                          : "text-[#172033] hover:bg-slate-50"
                      }`}
                    >
                      {item.name}
                    </Link>
                  );
                })}
              </div>
            );
          })}
        </nav>

        <div className="p-2.5 border-t border-[#E4E7EC] text-[10px] text-[#667085] text-center font-mono">
          System v1.0 • Live Telemetry
        </div>
      </aside>
    </>
  );
};
