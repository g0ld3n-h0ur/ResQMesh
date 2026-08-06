import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Home, 
  UserPlus, 
  UserMinus, 
  MapPin, 
  Phone, 
  Users, 
  AlertTriangle,
  CheckCircle2
} from "lucide-react";
import { api, unwrapList } from "../lib/api";

interface Shelter {
  id: string;
  shelter_name: string;
  capacity: number;
  current_occupancy: number;
  contact_number: string;
  district: string;
  state: string;
  latitude: number;
  longitude: number;
}

export const Shelters: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedShelterId, setSelectedShelterId] = useState<string | null>(null);
  const [countInput, setCountInput] = useState<number>(10);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // 1. Fetch Shelters
  const { data: shelters = [], isLoading, isError } = useQuery<Shelter[]>({
    queryKey: ["shelters-list"],
    queryFn: async () => unwrapList<Shelter>(await api.get("/shelters/")),
  });

  // 2. Checkin Mutation
  const checkinMutation = useMutation({
    mutationFn: async ({ id, count }: { id: string; count: number }) => {
      const res = await api.post(`/shelters/${id}/checkin`, { count });
      return res.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["shelters-list"] });
      setSuccessMsg(`Successfully checked in ${variables.count} evacuees!`);
      setSelectedShelterId(null);
      setTimeout(() => setSuccessMsg(null), 3000);
    },
    onError: (err: any) => {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || "Failed to check in evacuees. Capacity limit exceeded?");
      setTimeout(() => setErrorMsg(null), 4000);
    }
  });

  // 3. Checkout Mutation
  const checkoutMutation = useMutation({
    mutationFn: async ({ id, count }: { id: string; count: number }) => {
      const res = await api.post(`/shelters/${id}/checkout`, { count });
      return res.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["shelters-list"] });
      setSuccessMsg(`Successfully checked out ${variables.count} evacuees!`);
      setSelectedShelterId(null);
      setTimeout(() => setSuccessMsg(null), 3000);
    },
    onError: (err: any) => {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || "Failed to check out evacuees.");
      setTimeout(() => setErrorMsg(null), 4000);
    }
  });

  const handleAction = (id: string, type: "checkin" | "checkout") => {
    if (countInput <= 0) return;
    if (type === "checkin") {
      checkinMutation.mutate({ id, count: countInput });
    } else {
      checkoutMutation.mutate({ id, count: countInput });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-slate-800">Safe Shelters Directory</h2>
        <p className="text-xs text-slate-400">Manage capacities and logs for active disaster relief camp locations.</p>
      </div>

      <AnimatePresence>
        {/* Success/Error Alerts */}
        {successMsg && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span className="font-semibold">{successMsg}</span>
          </motion.div>
        )}
        {errorMsg && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-600" />
            <span className="font-semibold">{errorMsg}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading Skeletal state */}
      {isLoading && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-48 bg-slate-100 animate-pulse rounded-2xl border border-slate-200" />
          ))}
        </div>
      )}

      {/* Error state */}
      {isError && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-rose-600" />
          <span>Error syncing safe shelter databases. Please confirm server state.</span>
        </div>
      )}

      {/* Grid view */}
      {!isLoading && !isError && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {shelters.length > 0 ? (
            shelters.map((shelter) => {
              const spotsLeft = shelter.capacity - shelter.current_occupancy;
              const fillPercent = Math.min(100, Math.max(0, Math.round((shelter.current_occupancy / shelter.capacity) * 100)));
              
              const isFull = fillPercent >= 100;
              const isWarning = fillPercent >= 85 && !isFull;
              
              const progressColor = isFull 
                ? "bg-rose-500" 
                : isWarning 
                ? "bg-amber-500" 
                : "bg-indigo-600";

              const badgeColor = isFull 
                ? "bg-rose-50 border-rose-200 text-rose-800" 
                : isWarning 
                ? "bg-amber-50 border-amber-200 text-amber-800" 
                : "bg-emerald-50 border-emerald-200 text-emerald-800";

              const badgeText = isFull 
                ? "At Capacity" 
                : isWarning 
                ? "Near Limit" 
                : "Space Available";

              return (
                <div key={shelter.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4 flex flex-col justify-between">
                  {/* Title Header */}
                  <div>
                    <div className="flex items-start justify-between">
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${badgeColor}`}>
                        {badgeText}
                      </span>
                      <Home className="w-5 h-5 text-slate-400" />
                    </div>
                    <h3 className="text-base font-bold text-slate-800 mt-2.5 tracking-tight truncate" title={shelter.shelter_name}>
                      {shelter.shelter_name}
                    </h3>
                  </div>

                  {/* Occupancy details */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-[10px] text-slate-500 font-semibold">
                      <span>Occupied: {shelter.current_occupancy} / {shelter.capacity} spots</span>
                      <span>{spotsLeft} free</span>
                    </div>
                    <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div className={`h-full ${progressColor}`} style={{ width: `${fillPercent}%` }} />
                    </div>
                  </div>

                  {/* EOC Action Triggers */}
                  <div className="border-t border-slate-50 pt-3.5 space-y-3">
                    {selectedShelterId === shelter.id ? (
                      <div className="flex items-center space-x-2">
                        <input
                          type="number"
                          min="1"
                          value={countInput}
                          onChange={(e) => setCountInput(parseInt(e.target.value) || 0)}
                          className="w-16 px-2.5 py-1.5 border border-slate-200 rounded-lg text-xs font-semibold focus:outline-none"
                        />
                        <button
                          onClick={() => handleAction(shelter.id, "checkin")}
                          disabled={checkinMutation.isPending}
                          className="flex-1 flex items-center justify-center space-x-1 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-[10px] font-bold rounded-lg shadow-sm"
                        >
                          <UserPlus className="w-3.5 h-3.5" />
                          <span>In</span>
                        </button>
                        <button
                          onClick={() => handleAction(shelter.id, "checkout")}
                          disabled={checkoutMutation.isPending}
                          className="flex-1 flex items-center justify-center space-x-1 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-[10px] font-bold rounded-lg shadow-sm"
                        >
                          <UserMinus className="w-3.5 h-3.5" />
                          <span>Out</span>
                        </button>
                        <button
                          onClick={() => setSelectedShelterId(null)}
                          className="px-2 py-1.5 border border-slate-200 text-slate-500 text-[10px] font-bold rounded-lg hover:bg-slate-50"
                        >
                          X
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => {
                          setSelectedShelterId(shelter.id);
                          setCountInput(10);
                        }}
                        className="w-full flex items-center justify-center space-x-2 py-2 border border-indigo-100 hover:border-indigo-200 hover:bg-indigo-50/50 text-indigo-700 text-xs font-semibold rounded-xl transition"
                      >
                        <Users className="w-4 h-4" />
                        <span>Update Evacuees Count</span>
                      </button>
                    )}
                  </div>

                  {/* Metadata fields */}
                  <div className="flex items-center justify-between text-[9px] text-slate-400 font-semibold border-t border-slate-50 pt-3">
                    <span className="flex items-center space-x-1">
                      <MapPin className="w-3 h-3" />
                      <span className="truncate max-w-[100px]">{shelter.district}, {shelter.state}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Phone className="w-3 h-3" />
                      <span>{shelter.contact_number}</span>
                    </span>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="col-span-full bg-white border border-slate-200 border-dashed rounded-2xl p-12 text-center text-slate-400 text-xs">
              <Home className="w-12 h-12 text-slate-300 mx-auto mb-3 animate-pulse" />
              <span>No emergency safe shelters registered in coordinate database.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
