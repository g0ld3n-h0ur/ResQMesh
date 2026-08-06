import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { 
  HeartPulse, 
  MapPin, 
  Phone, 
  AlertTriangle,
  CheckCircle2,
  Edit2
} from "lucide-react";
import { api, unwrapList } from "../lib/api";

interface Hospital {
  id: string;
  hospital_name: string;
  latitude: number;
  longitude: number;
  available_beds: number;
  icu_beds: number;
  ventilators: number;
  ambulances: number;
  blood_units: number;
  oxygen_units: number;
  contact_number: string;
}

export const Hospitals: React.FC = () => {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [bedInput, setBedInput] = useState<number>(0);
  const [icuInput, setIcuInput] = useState<number>(0);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // 1. Fetch Hospitals
  const { data: hospitals = [], isLoading, isError } = useQuery<Hospital[]>({
    queryKey: ["hospitals-list"],
    queryFn: async () => unwrapList<Hospital>(await api.get("/hospitals/")),
  });

  // 2. Availability Mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, available_beds, icu_beds }: { id: string; available_beds: number; icu_beds: number }) => {
      const res = await api.patch(`/hospitals/${id}/availability`, { available_beds, icu_beds });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hospitals-list"] });
      setSuccessMsg(`Successfully updated hospital capacities!`);
      setEditingId(null);
      setTimeout(() => setSuccessMsg(null), 3000);
    },
    onError: (err: any) => {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || "Failed to update hospital metrics.");
      setTimeout(() => setErrorMsg(null), 4000);
    }
  });

  const handleUpdateSubmit = (e: React.FormEvent, id: string) => {
    e.preventDefault();
    updateMutation.mutate({
      id,
      available_beds: bedInput,
      icu_beds: icuInput
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-slate-800">Hospital Capacity Fleet</h2>
        <p className="text-xs text-slate-400">Monitor and update critical care parameters, ICU bed grids, and ventilator volumes.</p>
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

      {/* Loading state */}
      {isLoading && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-56 bg-slate-100 animate-pulse rounded-2xl border border-slate-200" />
          ))}
        </div>
      )}

      {/* Error state */}
      {isError && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-rose-600" />
          <span>Error sync hospital telemetry reports. Confirm local backend uvicorn is running.</span>
        </div>
      )}

      {/* Grid listing */}
      {!isLoading && !isError && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {hospitals.length > 0 ? (
            hospitals.map((hospital) => {
              const isEditing = editingId === hospital.id;

              return (
                <div key={hospital.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4 flex flex-col justify-between">
                  {/* Header Title */}
                  <div className="flex items-start justify-between">
                    <h3 className="text-sm font-bold text-slate-800 tracking-tight leading-snug truncate pr-2" title={hospital.hospital_name}>
                      {hospital.hospital_name}
                    </h3>
                    <div className="p-2 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-600 flex-shrink-0">
                      <HeartPulse className="w-5 h-5" />
                    </div>
                  </div>

                  {/* Operational Telemetry Grid */}
                  <div className="grid grid-cols-2 gap-3.5 bg-slate-50 border border-slate-100 p-3 rounded-xl">
                    <div className="text-center">
                      <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider block">Beds Available</span>
                      <span className="text-lg font-black text-cyan-600 block mt-0.5">{hospital.available_beds}</span>
                    </div>
                    <div className="text-center border-l border-slate-200">
                      <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider block">ICU Beds</span>
                      <span className="text-lg font-black text-rose-500 block mt-0.5">{hospital.icu_beds}</span>
                    </div>
                  </div>

                  {/* Inline Edit Form */}
                  <div className="border-t border-slate-50 pt-3">
                    {isEditing ? (
                      <form onSubmit={(e) => handleUpdateSubmit(e, hospital.id)} className="space-y-3">
                        <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-1">
                            <label className="text-[9px] font-bold text-slate-500">General Beds</label>
                            <input
                              type="number"
                              value={bedInput}
                              onChange={(e) => setBedInput(parseInt(e.target.value) || 0)}
                              className="w-full px-2.5 py-1.5 border border-slate-200 rounded-lg text-xs"
                              required
                            />
                          </div>
                          <div className="space-y-1">
                            <label className="text-[9px] font-bold text-slate-500">ICU Beds</label>
                            <input
                              type="number"
                              value={icuInput}
                              onChange={(e) => setIcuInput(parseInt(e.target.value) || 0)}
                              className="w-full px-2.5 py-1.5 border border-slate-200 rounded-lg text-xs"
                              required
                            />
                          </div>
                        </div>
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            type="button"
                            onClick={() => setEditingId(null)}
                            className="px-2.5 py-1.5 border border-slate-200 text-slate-600 text-[10px] font-semibold rounded-lg hover:bg-slate-50"
                          >
                            Cancel
                          </button>
                          <button
                            type="submit"
                            disabled={updateMutation.isPending}
                            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-[10px] font-bold rounded-lg shadow-sm"
                          >
                            Save
                          </button>
                        </div>
                      </form>
                    ) : (
                      <button
                        onClick={() => {
                          setEditingId(hospital.id);
                          setBedInput(hospital.available_beds);
                          setIcuInput(hospital.icu_beds);
                        }}
                        className="w-full flex items-center justify-center space-x-2 py-2 border border-indigo-100 hover:border-indigo-200 hover:bg-indigo-50/50 text-indigo-700 text-xs font-semibold rounded-xl transition"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                        <span>Edit Bed Availability</span>
                      </button>
                    )}
                  </div>

                  {/* Resource Aggregation Badges */}
                  <div className="grid grid-cols-4 gap-1.5 text-center text-[9px] font-bold text-slate-500 pt-3 border-t border-slate-50">
                    <div className="bg-slate-50 p-1 rounded">
                      <div>Vent</div>
                      <div className="text-slate-800 mt-0.5">{hospital.ventilators}</div>
                    </div>
                    <div className="bg-slate-50 p-1 rounded">
                      <div>Amb</div>
                      <div className="text-slate-800 mt-0.5">{hospital.ambulances}</div>
                    </div>
                    <div className="bg-slate-50 p-1 rounded">
                      <div>Blood</div>
                      <div className="text-slate-800 mt-0.5">{hospital.blood_units}u</div>
                    </div>
                    <div className="bg-slate-50 p-1 rounded">
                      <div>Oxy</div>
                      <div className="text-slate-800 mt-0.5">{hospital.oxygen_units}u</div>
                    </div>
                  </div>

                  {/* Bottom Metadata */}
                  <div className="flex items-center justify-between text-[9px] text-slate-400 font-semibold pt-3.5 border-t border-slate-50">
                    <span className="flex items-center space-x-1">
                      <MapPin className="w-3 h-3" />
                      <span>{hospital.latitude.toFixed(3)}, {hospital.longitude.toFixed(3)}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Phone className="w-3 h-3" />
                      <span>{hospital.contact_number}</span>
                    </span>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="col-span-full bg-white border border-slate-200 border-dashed rounded-2xl p-12 text-center text-slate-400 text-xs">
              <HeartPulse className="w-12 h-12 text-slate-300 mx-auto mb-3 animate-pulse" />
              <span>No hospitals registered in coordination system database.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
