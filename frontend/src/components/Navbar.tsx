import React from "react";
import { useLocation } from "react-router-dom";
import { Menu, Bell, User } from "lucide-react";

interface NavbarProps {
  onMenuToggle: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onMenuToggle }) => {
  const location = useLocation();

  const getPageTitle = () => {
    switch (location.pathname) {
      case "/":
        return "Command Center Dashboard";
      case "/prediction":
        return "AI Risk & Flood Prediction";
      case "/resources":
        return "Resource Inventory & Allocation";
      case "/shelters":
        return "Emergency Shelter Coordinator";
      case "/hospitals":
        return "Hospital Fleet & Capacity";
      case "/reports":
        return "Citizen Distress Incident Reports";
      case "/settings":
        return "Portal System Settings";
      default:
        return "ResQMesh Portal";
    }
  };

  return (
    <header className="flex items-center justify-between h-16 px-6 bg-white border-b border-slate-200 shadow-sm z-30">
      <div className="flex items-center space-x-4">
        <button
          className="p-2 rounded-md hover:bg-slate-100 lg:hidden focus:outline-none"
          onClick={onMenuToggle}
        >
          <Menu className="w-5 h-5 text-slate-600" />
        </button>
        <h1 className="text-xl font-semibold text-slate-800 tracking-tight">
          {getPageTitle()}
        </h1>
      </div>

      <div className="flex items-center space-x-4">
        <button className="relative p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-50 rounded-full transition-colors duration-150">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full border border-white" />
        </button>

        <div className="h-6 w-px bg-slate-200" />

        <div className="flex items-center space-x-3">
          <div className="flex flex-col text-right hidden sm:flex">
            <span className="text-sm font-semibold text-slate-800">Gov. Command Unit</span>
            <span className="text-xs text-indigo-600 font-medium">Administrator</span>
          </div>
          <div className="w-9 h-9 rounded-full bg-slate-100 flex items-center justify-center border border-slate-200 text-slate-600 cursor-pointer hover:bg-slate-200 transition-colors duration-150">
            <User className="w-4 h-4" />
          </div>
        </div>
      </div>
    </header>
  );
};
