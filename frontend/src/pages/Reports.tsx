import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { 
  FileText, 
  MapPin, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Link as LinkIcon,
  X
} from "lucide-react";
import { api, unwrapList } from "../lib/api";

interface EmergencyReport {
  id: string;
  reporter_name: string;
  phone: string;
  disaster_type: string;
  latitude: number;
  longitude: number;
  address: string;
  description: string;
  is_verified: boolean;
  linked_disaster_id: string | null;
  created_at: string;
}

interface Disaster {
  id: string;
  title: string;
  severity: string;
  status: string;
}

export const Reports: React.FC = () => {
  const queryClient = useQueryClient();
  const [verifyingId, setVerifyingId] = useState<string | null>(null);
  const [selectedDisasterId, setSelectedDisasterId] = useState<string>("");
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // 1. Fetch Reports
  const { data: reports = [], isLoading: isReportsLoading, isError: isReportsError } = useQuery<EmergencyReport[]>({
    queryKey: ["reports-list"],
    queryFn: async () => unwrapList<EmergencyReport>(await api.get("/reports/")),
  });

  // 2. Fetch Active Disasters for linking
  const { data: disasters = [] } = useQuery<Disaster[]>({
    queryKey: ["disasters-list"],
    queryFn: async () => unwrapList<Disaster>(await api.get("/disasters/")),
  });

  // 3. Verify Report Mutation
  const verifyMutation = useMutation({
    mutationFn: async ({ id, linked_disaster_id }: { id: string; linked_disaster_id: string }) => {
      const res = await api.patch(`/reports/${id}/verify`, {
        is_verified: true,
        linked_disaster_id
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports-list"] });
      setSuccessMsg("SOS Report verified and linked successfully!");
      setVerifyingId(null);
      setSelectedDisasterId("");
      setTimeout(() => setSuccessMsg(null), 3000);
    },
    onError: (err: any) => {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || "Failed to verify SOS report.");
      setTimeout(() => setErrorMsg(null), 4000);
    }
  });

  const handleVerifySubmit = (e: React.FormEvent, reportId: string) => {
    e.preventDefault();
    if (!selectedDisasterId) return;
    verifyMutation.mutate({
      id: reportId,
      linked_disaster_id: selectedDisasterId
    });
  };

  const activeDisasters = disasters.filter(d => d.status !== "resolved");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-slate-800">Distress SOS Registry</h2>
        <p className="text-xs text-slate-400">Review incoming citizen incident filings, audit report coordinates, and verify operational linkages.</p>
      </div>

      <AnimatePresence>
        {/* Success/Error Banners */}
        {successMsg && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
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
      {isReportsLoading && (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-28 bg-slate-100 animate-pulse rounded-2xl border border-slate-200" />
          ))}
        </div>
      )}

      {/* Error state */}
      {isReportsError && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-rose-600" />
          <span>Error sync distress report feeds. Please check backend connection.</span>
        </div>
      )}

      {/* List items */}
      {!isReportsLoading && !isReportsError && (
        <div className="space-y-4">
          {reports.length > 0 ? (
            reports.map((report) => {
              const isVerifying = verifyingId === report.id;
              
              return (
                <div key={report.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  
                  {/* Left Column: Reporter Metadata */}
                  <div className="space-y-2 md:max-w-md">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 rounded bg-indigo-50 border border-indigo-100 text-indigo-700 text-[10px] font-bold uppercase tracking-wider">
                        {report.disaster_type}
                      </span>
                      {report.is_verified ? (
                        <span className="flex items-center space-x-1 text-emerald-600 text-[10px] font-bold">
                          <CheckCircle className="w-3.5 h-3.5" />
                          <span>Verified & Linked</span>
                        </span>
                      ) : (
                        <span className="flex items-center space-x-1 text-amber-500 text-[10px] font-bold">
                          <Clock className="w-3.5 h-3.5" />
                          <span>Awaiting Action</span>
                        </span>
                      )}
                    </div>
                    
                    <h3 className="text-sm font-bold text-slate-800">
                      {report.reporter_name} <span className="text-xs text-slate-400 font-medium">({report.phone})</span>
                    </h3>
                    
                    <p className="text-xs text-slate-600 leading-relaxed font-medium">
                      "{report.description}"
                    </p>
                  </div>

                  {/* Middle Column: Location & Coord */}
                  <div className="flex flex-col text-xs text-slate-500 space-y-1.5 min-w-[150px]">
                    <span className="flex items-center space-x-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      <span className="font-semibold text-slate-700 truncate max-w-[150px]">{report.address}</span>
                    </span>
                    <span className="text-[10px] font-medium pl-5">
                      GPS: {report.latitude.toFixed(4)}, {report.longitude.toFixed(4)}
                    </span>
                  </div>

                  {/* Right Column: Verification Panel */}
                  <div className="flex items-center justify-end min-w-[240px]">
                    {isVerifying ? (
                      <form onSubmit={(e) => handleVerifySubmit(e, report.id)} className="flex items-center space-x-2 bg-slate-50 p-2 border border-slate-100 rounded-xl">
                        <select
                          value={selectedDisasterId}
                          onChange={(e) => setSelectedDisasterId(e.target.value)}
                          className="px-2 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-semibold focus:outline-none"
                          required
                        >
                          <option value="">Select Disaster Link</option>
                          {activeDisasters.map(d => (
                            <option key={d.id} value={d.id}>{d.title}</option>
                          ))}
                        </select>
                        <button
                          type="submit"
                          className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-[10px] font-bold rounded-lg shadow-sm"
                        >
                          Link
                        </button>
                        <button
                          type="button"
                          onClick={() => setVerifyingId(null)}
                          className="p-1.5 border border-slate-200 text-slate-500 rounded-lg hover:bg-slate-50"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </form>
                    ) : (
                      !report.is_verified && (
                        <button
                          onClick={() => {
                            setVerifyingId(report.id);
                            setSelectedDisasterId("");
                          }}
                          className="flex items-center space-x-1.5 px-4 py-2 border border-emerald-600 hover:bg-emerald-50 text-emerald-700 text-xs font-semibold rounded-xl transition"
                        >
                          <LinkIcon className="w-3.5 h-3.5" />
                          <span>Link to Active Disaster</span>
                        </button>
                      )
                    )}
                  </div>

                </div>
              );
            })
          ) : (
            <div className="bg-white border border-slate-200 border-dashed rounded-2xl p-12 text-center text-slate-400 text-xs">
              <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3 animate-pulse" />
              <span>No incident distress filings registered.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
