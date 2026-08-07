import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Package,
  Plus,
  MapPin,
  CheckCircle,
  AlertTriangle,
  Sparkles,
  ArrowRight
} from "lucide-react";
import { api, formatApiError, unwrapList } from "../lib/api";

interface Resource {
  id: string;
  resource_type: string;
  quantity: number;
  available_quantity: number;
  location: string | null;
  status: string;
}

interface AllocationSuggestion {
  resource_id: string;
  resource_type: string;
  resource_location: string | null;
  source_available_quantity: number;
  disaster_id: string;
  disaster_title: string;
  disaster_need_rank: number;
  disaster_need_score: number;
  suggested_quantity: number;
  rationale: string;
}

const RESOURCE_UNITS: Record<string, string> = {
  food_packet: "packets",
  food: "packets",
  drinking_water: "liters",
  water: "liters",
  medical_kit: "kits",
  medicine: "units",
  rescue_boat: "boats",
  vehicles: "units",
  generator: "units",
  blankets: "units",
  fuel: "liters",
};

const DEFAULT_UNITS: Record<string, string> = {
  food_packet: "packets",
  drinking_water: "liters",
  rescue_boat: "boats",
  medical_kit: "kits",
  generator: "units",
};

function formatResourceLabel(type: string): string {
  return type.replaceAll("_", " ");
}


export const ResourceAllocation: React.FC = () => {
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    resource_type: "food_packet",
    quantity: 500,
    unit: "packets",
    location: "Main Depot Chennai",
    latitude: 13.0827,
    longitude: 80.2707
  });

  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const { data: resources = [], isLoading, isError } = useQuery<Resource[]>({
    queryKey: ["resources-list"],
    queryFn: async () => unwrapList<Resource>(await api.get("/resources/")),
  });

  const {
    data: suggestions = [],
    isLoading: isSuggestionsLoading,
    isError: isSuggestionsError,
  } = useQuery<AllocationSuggestion[]>({
    queryKey: ["allocation-suggestions"],
    queryFn: async () => unwrapList<AllocationSuggestion>(await api.get("/resources/allocation-suggestions")),
  });

  const [applyError, setApplyError] = useState<string | null>(null);
  const [appliedKeys, setAppliedKeys] = useState<Set<string>>(new Set());

  const applyMutation = useMutation({
    mutationFn: async (suggestion: AllocationSuggestion) => {
      const res = await api.patch(`/resources/${suggestion.resource_id}/allocate`, {
        disaster_id: suggestion.disaster_id,
        quantity_to_allocate: suggestion.suggested_quantity,
      });
      return res.data;
    },
    onSuccess: (_, suggestion) => {
      queryClient.invalidateQueries({ queryKey: ["resources-list"] });
      queryClient.invalidateQueries({ queryKey: ["allocation-suggestions"] });
      setAppliedKeys((prev) => new Set(prev).add(`${suggestion.resource_id}:${suggestion.disaster_id}`));
    },
    onError: (err: unknown) => {
      console.error(err);
      setApplyError(formatApiError(err, "Failed to apply suggested allocation."));
      setTimeout(() => setApplyError(null), 5000);
    },
  });

  const createMutation = useMutation({
    mutationFn: async (payload: {
      resource_type: string;
      quantity: number;
      available_quantity: number;
      location: string;
      status: string;
    }) => {
      const res = await api.post("/resources/", payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resources-list"] });
      setFormSuccess(`Relief supply "${formatResourceLabel(formData.resource_type)}" added successfully!`);
      setShowAddForm(false);
      setFormData({
        resource_type: "food_packet",
        quantity: 500,
        unit: "packets",
        location: "Main Depot Chennai",
        latitude: 13.0827,
        longitude: 80.2707
      });
      setTimeout(() => setFormSuccess(null), 3000);
    },
    onError: (err: unknown) => {
      console.error(err);
      setFormError(formatApiError(err, "Failed to register resource."));
      setTimeout(() => setFormError(null), 5000);
    }
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    if (name === "resource_type") {
      setFormData(prev => ({
        ...prev,
        resource_type: value,
        unit: DEFAULT_UNITS[value] ?? "units",
      }));
      return;
    }
    setFormData(prev => ({
      ...prev,
      [name]: name === "quantity" || name === "latitude" || name === "longitude" ? parseFloat(value) || 0 : value
    }));
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      resource_type: formData.resource_type,
      quantity: formData.quantity,
      available_quantity: formData.quantity,
      location: formData.location,
      status: "available",
    });
  };

  const getResourceMeta = (type: string) => {
    switch (type?.toLowerCase()) {
      case "rescue_boat":
      case "vehicles":
        return { bg: "bg-blue-50 border-blue-200", text: "text-blue-700", fill: "bg-blue-600" };
      case "food_packet":
      case "food":
        return { bg: "bg-amber-50 border-amber-200", text: "text-amber-700", fill: "bg-amber-600" };
      case "drinking_water":
      case "water":
        return { bg: "bg-cyan-50 border-cyan-200", text: "text-cyan-700", fill: "bg-cyan-600" };
      case "medical_kit":
      case "medicine":
        return { bg: "bg-rose-50 border-rose-200", text: "text-rose-700", fill: "bg-rose-600" };
      default:
        return { bg: "bg-purple-50 border-purple-200", text: "text-purple-700", fill: "bg-purple-600" };
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-800">EOC Supplies & Resource Pools</h2>
          <p className="text-xs text-slate-400">Monitor active disaster response assets and register incoming relief payloads.</p>
        </div>

        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center space-x-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          <span>Register New Inventory</span>
        </button>
      </div>

      <AnimatePresence>
        {formSuccess && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            <span className="font-semibold">{formSuccess}</span>
          </motion.div>
        )}
        {formError && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-600" />
            <span className="font-semibold">{formError}</span>
          </motion.div>
        )}

        {showAddForm && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }} 
            animate={{ height: "auto", opacity: 1 }} 
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4"
          >
            <h3 className="text-sm font-semibold text-slate-800">Inventory Registration Form</h3>
            <form onSubmit={handleFormSubmit} className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-700">Supply Type</label>
                <select 
                  name="resource_type" 
                  value={formData.resource_type} 
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-xs focus:outline-none focus:border-indigo-500 font-semibold"
                >
                  <option value="food_packet">Food Packets</option>
                  <option value="drinking_water">Drinking Water</option>
                  <option value="rescue_boat">Rescue Boats</option>
                  <option value="medical_kit">Medical Kits</option>
                  <option value="generator">Emergency Generators</option>
                  <option value="medicine">Medicine</option>
                  <option value="blankets">Blankets</option>
                  <option value="fuel">Fuel</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-700">Quantity</label>
                <input 
                  type="number" 
                  name="quantity" 
                  min={1}
                  value={formData.quantity} 
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-xs focus:outline-none" 
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-700">Measurement Unit</label>
                <input 
                  type="text" 
                  name="unit" 
                  value={formData.unit} 
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-xs focus:outline-none"
                  placeholder="e.g. packets, units, liters"
                  readOnly
                />
              </div>

              <div className="space-y-1.5 sm:col-span-2 lg:col-span-3">
                <label className="text-xs font-semibold text-slate-700">Warehouse Location</label>
                <input 
                  type="text" 
                  name="location" 
                  value={formData.location} 
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-xs focus:outline-none"
                  required
                />
              </div>

              <div className="sm:col-span-2 lg:col-span-3 flex items-center justify-end space-x-3 pt-4 border-t border-slate-100">
                <button 
                  type="button" 
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 text-xs font-semibold rounded-xl hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  disabled={createMutation.isPending}
                  className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl disabled:opacity-50"
                >
                  {createMutation.isPending ? "Submitting..." : "Submit Stock"}
                </button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Suggested Allocations — optimization output */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex items-start space-x-2">
          <div className="p-2 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-600 flex-shrink-0">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-800">Suggested Allocations</h3>
            <p className="text-xs text-slate-400">
              Unassigned stock split across active disasters, weighted by computed need score. Review and apply.
            </p>
          </div>
        </div>

        {applyError && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{applyError}</span>
          </div>
        )}

        {isSuggestionsLoading && (
          <div className="space-y-2">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="h-16 bg-slate-100 animate-pulse rounded-xl" />
            ))}
          </div>
        )}

        {isSuggestionsError && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl">
            Error computing allocation suggestions.
          </div>
        )}

        {!isSuggestionsLoading && !isSuggestionsError && (
          suggestions.length > 0 ? (
            <div className="space-y-2.5">
              {suggestions.map((s) => {
                const key = `${s.resource_id}:${s.disaster_id}`;
                const applied = appliedKeys.has(key);
                return (
                  <div
                    key={key}
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 bg-slate-50 border border-slate-100 rounded-xl"
                  >
                    <div className="flex items-center space-x-2 text-xs">
                      <span className="px-2 py-0.5 rounded bg-white border border-slate-200 font-bold text-slate-700 uppercase tracking-wider text-[10px]">
                        {s.suggested_quantity} {formatResourceLabel(s.resource_type)}
                      </span>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                      <span className="font-semibold text-slate-700">{s.disaster_title}</span>
                      <span className="text-[10px] text-slate-400 font-semibold">
                        (need #{s.disaster_need_rank}, score {s.disaster_need_score})
                      </span>
                    </div>
                    <button
                      onClick={() => applyMutation.mutate(s)}
                      disabled={applied || applyMutation.isPending}
                      className={`flex-shrink-0 px-3 py-1.5 text-[10px] font-bold rounded-lg shadow-sm transition ${
                        applied
                          ? "bg-emerald-50 border border-emerald-200 text-emerald-700 cursor-default"
                          : "bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-50"
                      }`}
                    >
                      {applied ? "Applied" : "Apply"}
                    </button>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-xs text-slate-400">No unassigned stock to suggest right now — everything available is already committed.</p>
          )
        )}
      </div>

      {isLoading && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-44 bg-slate-100 animate-pulse rounded-2xl border border-slate-200" />
          ))}
        </div>
      )}

      {isError && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-rose-600" />
          <span>Error loading resource pools. Make sure the backend is running on port 8000 and you are logged in.</span>
        </div>
      )}

      {!isLoading && !isError && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {resources.length > 0 ? (
            resources.map((item) => {
              const meta = getResourceMeta(item.resource_type);
              const unit = RESOURCE_UNITS[item.resource_type] ?? "units";
              const percent = item.quantity > 0
                ? Math.min(100, Math.max(0, Math.round((item.available_quantity / item.quantity) * 100)))
                : 0;
              
              return (
                <div key={item.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4 flex flex-col justify-between">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${meta.bg} ${meta.text}`}>
                        {formatResourceLabel(item.resource_type)}
                      </span>
                      <h3 className="text-lg font-bold text-slate-800 mt-2">
                        {item.available_quantity} <span className="text-xs text-slate-500 font-medium">{unit} available</span>
                      </h3>
                      <p className="text-[10px] text-slate-400 font-semibold uppercase mt-1">{item.status.replaceAll("_", " ")}</p>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 text-slate-600">
                      <Package className="w-5 h-5" />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-[10px] text-slate-500 font-semibold">
                      <span>Inventory Level: {percent}%</span>
                      <span>Total: {item.quantity} {unit}</span>
                    </div>
                    <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div className={`h-full ${meta.fill}`} style={{ width: `${percent}%` }} />
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-slate-400 font-semibold pt-3 border-t border-slate-50">
                    <span className="flex items-center space-x-1">
                      <MapPin className="w-3.5 h-3.5" />
                      <span>{item.location ?? "Location not set"}</span>
                    </span>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="col-span-full bg-white border border-slate-200 border-dashed rounded-2xl p-12 text-center text-slate-400 text-xs">
              <Package className="w-12 h-12 text-slate-300 mx-auto mb-3 animate-pulse" />
              <span>No relief supplies registered yet. Run the database seed or click &quot;Register New Inventory&quot; to add stock.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
