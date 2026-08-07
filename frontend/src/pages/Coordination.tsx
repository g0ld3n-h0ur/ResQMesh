import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Link2,
  Plus,
  AlertTriangle,
  CheckCircle,
  Clock,
  PlayCircle,
  XCircle,
  User,
  Building2,
  HeartPulse,
  Package,
} from "lucide-react";
import { api, formatApiError, unwrapList } from "../lib/api";

interface Assignment {
  id: string;
  disaster_id: string;
  volunteer_id: string | null;
  ngo_id: string | null;
  hospital_id: string | null;
  resource_id: string | null;
  status: "pending" | "in_progress" | "completed" | "cancelled";
  assigned_at: string;
}

interface Disaster {
  id: string;
  title: string;
  status: string;
}

interface PublicUser {
  id: string;
  full_name: string;
  role: string;
}

interface Hospital {
  id: string;
  hospital_name: string;
}

interface Resource {
  id: string;
  resource_type: string;
  location: string | null;
}

type AssigneeType = "volunteer" | "ngo" | "hospital" | "resource";

const STATUS_STYLES: Record<Assignment["status"], { badge: string; icon: React.ElementType }> = {
  pending: { badge: "bg-amber-50 border-amber-200 text-amber-800", icon: Clock },
  in_progress: { badge: "bg-indigo-50 border-indigo-200 text-indigo-800", icon: PlayCircle },
  completed: { badge: "bg-emerald-50 border-emerald-200 text-emerald-800", icon: CheckCircle },
  cancelled: { badge: "bg-slate-100 border-slate-200 text-slate-500", icon: XCircle },
};

const NEXT_TRANSITIONS: Record<Assignment["status"], { label: string; target: Assignment["status"] }[]> = {
  pending: [
    { label: "Start", target: "in_progress" },
    { label: "Cancel", target: "cancelled" },
  ],
  in_progress: [
    { label: "Complete", target: "completed" },
    { label: "Cancel", target: "cancelled" },
  ],
  completed: [],
  cancelled: [],
};

const ASSIGNEE_TYPE_META: Record<AssigneeType, { label: string; icon: React.ElementType }> = {
  volunteer: { label: "Volunteer", icon: User },
  ngo: { label: "NGO", icon: Building2 },
  hospital: { label: "Hospital", icon: HeartPulse },
  resource: { label: "Resource", icon: Package },
};

export const Coordination: React.FC = () => {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [filterDisaster, setFilterDisaster] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [formDisaster, setFormDisaster] = useState("");
  const [assigneeType, setAssigneeType] = useState<AssigneeType>("volunteer");
  const [assigneeId, setAssigneeId] = useState("");
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { data: assignments = [], isLoading, isError } = useQuery<Assignment[]>({
    queryKey: ["assignments-list", filterDisaster, filterStatus],
    queryFn: async () =>
      unwrapList<Assignment>(
        await api.get("/assignments/", {
          params: {
            ...(filterDisaster ? { disaster_id: filterDisaster } : {}),
            ...(filterStatus ? { status: filterStatus } : {}),
          },
        })
      ),
    refetchInterval: 20_000,
  });

  const { data: disasters = [] } = useQuery<Disaster[]>({
    queryKey: ["disasters-list"],
    queryFn: async () => unwrapList<Disaster>(await api.get("/disasters/")),
  });

  const { data: volunteers = [] } = useQuery<PublicUser[]>({
    queryKey: ["users-list", "volunteer"],
    queryFn: async () => unwrapList<PublicUser>(await api.get("/users/", { params: { role: "volunteer" } })),
  });

  const { data: ngos = [] } = useQuery<PublicUser[]>({
    queryKey: ["users-list", "ngo"],
    queryFn: async () => unwrapList<PublicUser>(await api.get("/users/", { params: { role: "ngo" } })),
  });

  const { data: hospitals = [] } = useQuery<Hospital[]>({
    queryKey: ["hospitals-list"],
    queryFn: async () => unwrapList<Hospital>(await api.get("/hospitals/")),
  });

  const { data: resources = [] } = useQuery<Resource[]>({
    queryKey: ["resources-list"],
    queryFn: async () => unwrapList<Resource>(await api.get("/resources/")),
  });

  const disasterMap = React.useMemo(() => Object.fromEntries(disasters.map((d) => [d.id, d.title])), [disasters]);
  const volunteerMap = React.useMemo(() => Object.fromEntries(volunteers.map((u) => [u.id, u.full_name])), [volunteers]);
  const ngoMap = React.useMemo(() => Object.fromEntries(ngos.map((u) => [u.id, u.full_name])), [ngos]);
  const hospitalMap = React.useMemo(() => Object.fromEntries(hospitals.map((h) => [h.id, h.hospital_name])), [hospitals]);
  const resourceMap = React.useMemo(
    () => Object.fromEntries(resources.map((r) => [r.id, `${r.resource_type.replaceAll("_", " ")} (${r.location ?? "no location"})`])),
    [resources]
  );

  const assigneeOptions: Record<AssigneeType, { id: string; label: string }[]> = {
    volunteer: volunteers.map((u) => ({ id: u.id, label: u.full_name })),
    ngo: ngos.map((u) => ({ id: u.id, label: u.full_name })),
    hospital: hospitals.map((h) => ({ id: h.id, label: h.hospital_name })),
    resource: resources.map((r) => ({ id: r.id, label: `${r.resource_type.replaceAll("_", " ")} — ${r.location ?? "no location"}` })),
  };

  const resolveAssignee = (a: Assignment): { type: AssigneeType; name: string } | null => {
    if (a.volunteer_id) return { type: "volunteer", name: volunteerMap[a.volunteer_id] ?? "Unknown volunteer" };
    if (a.ngo_id) return { type: "ngo", name: ngoMap[a.ngo_id] ?? "Unknown NGO" };
    if (a.hospital_id) return { type: "hospital", name: hospitalMap[a.hospital_id] ?? "Unknown hospital" };
    if (a.resource_id) return { type: "resource", name: resourceMap[a.resource_id] ?? "Unknown resource" };
    return null;
  };

  const createMutation = useMutation({
    mutationFn: async () => {
      const payload: Record<string, string> = { disaster_id: formDisaster };
      payload[`${assigneeType}_id`] = assigneeId;
      const res = await api.post("/assignments/", payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments-list"] });
      setSuccessMsg("Assignment created successfully!");
      setShowForm(false);
      setFormDisaster("");
      setAssigneeId("");
      setTimeout(() => setSuccessMsg(null), 3000);
    },
    onError: (err: unknown) => {
      setErrorMsg(formatApiError(err, "Failed to create assignment."));
      setTimeout(() => setErrorMsg(null), 5000);
    },
  });

  const statusMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: Assignment["status"] }) => {
      const res = await api.patch(`/assignments/${id}/status`, { status });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments-list"] });
    },
    onError: (err: unknown) => {
      setErrorMsg(formatApiError(err, "Failed to update assignment status."));
      setTimeout(() => setErrorMsg(null), 5000);
    },
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formDisaster || !assigneeId) return;
    createMutation.mutate();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-800">Cross-Org Coordination</h2>
          <p className="text-xs text-slate-400">
            Assign volunteers, NGOs, hospitals, and resources to active disasters, and track task status across every organization.
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center space-x-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          <span>New Assignment</span>
        </button>
      </div>

      <AnimatePresence>
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

        {showForm && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4"
          >
            <h3 className="text-sm font-semibold text-slate-800">New Assignment</h3>
            <form onSubmit={handleCreateSubmit} className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-700">Disaster</label>
                <select
                  value={formDisaster}
                  onChange={(e) => setFormDisaster(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-xs focus:outline-none font-semibold"
                  required
                >
                  <option value="">Select disaster</option>
                  {disasters.map((d) => (
                    <option key={d.id} value={d.id}>{d.title}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-700">Assignee Type</label>
                <select
                  value={assigneeType}
                  onChange={(e) => {
                    setAssigneeType(e.target.value as AssigneeType);
                    setAssigneeId("");
                  }}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-xs focus:outline-none font-semibold"
                >
                  {(Object.keys(ASSIGNEE_TYPE_META) as AssigneeType[]).map((t) => (
                    <option key={t} value={t}>{ASSIGNEE_TYPE_META[t].label}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5 sm:col-span-2">
                <label className="text-xs font-semibold text-slate-700">{ASSIGNEE_TYPE_META[assigneeType].label}</label>
                <select
                  value={assigneeId}
                  onChange={(e) => setAssigneeId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-xs focus:outline-none font-semibold"
                  required
                >
                  <option value="">Select {ASSIGNEE_TYPE_META[assigneeType].label.toLowerCase()}</option>
                  {assigneeOptions[assigneeType].map((opt) => (
                    <option key={opt.id} value={opt.id}>{opt.label}</option>
                  ))}
                </select>
                {assigneeOptions[assigneeType].length === 0 && (
                  <p className="text-[10px] text-amber-600">No {ASSIGNEE_TYPE_META[assigneeType].label.toLowerCase()}s available to assign.</p>
                )}
              </div>

              <div className="sm:col-span-2 flex items-center justify-end space-x-3 pt-4 border-t border-slate-100">
                <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 border border-slate-200 text-slate-600 text-xs font-semibold rounded-xl hover:bg-slate-50">
                  Cancel
                </button>
                <button type="submit" disabled={createMutation.isPending} className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl disabled:opacity-50">
                  {createMutation.isPending ? "Creating..." : "Create Assignment"}
                </button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={filterDisaster}
          onChange={(e) => setFilterDisaster(e.target.value)}
          className="px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 focus:outline-none"
        >
          <option value="">All disasters</option>
          {disasters.map((d) => (
            <option key={d.id} value={d.id}>{d.title}</option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 focus:outline-none"
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-20 bg-slate-100 animate-pulse rounded-2xl border border-slate-200" />
          ))}
        </div>
      )}

      {isError && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-rose-600" />
          <span>Error loading assignments. Confirm the backend is running.</span>
        </div>
      )}

      {!isLoading && !isError && (
        <div className="space-y-3">
          {assignments.length > 0 ? (
            assignments.map((a) => {
              const assignee = resolveAssignee(a);
              const AssigneeIcon = assignee ? ASSIGNEE_TYPE_META[assignee.type].icon : Link2;
              const StatusIcon = STATUS_STYLES[a.status].icon;
              const transitions = NEXT_TRANSITIONS[a.status];

              return (
                <div key={a.id} className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center space-x-3 min-w-0">
                    <div className="p-2 bg-slate-50 border border-slate-100 rounded-xl text-slate-600 flex-shrink-0">
                      <AssigneeIcon className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-slate-800 truncate">
                        {assignee ? assignee.name : "Unassigned"}
                        <span className="text-slate-400 font-medium"> → {disasterMap[a.disaster_id] ?? "Unknown disaster"}</span>
                      </p>
                      <p className="text-[10px] text-slate-400 font-semibold">
                        {assignee ? ASSIGNEE_TYPE_META[assignee.type].label : "—"} · {new Date(a.assigned_at).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 flex-shrink-0">
                    <span className={`flex items-center space-x-1 px-2.5 py-1 rounded text-[10px] font-bold uppercase tracking-wider border ${STATUS_STYLES[a.status].badge}`}>
                      <StatusIcon className="w-3 h-3" />
                      <span>{a.status.replace("_", " ")}</span>
                    </span>
                    {transitions.map((t) => (
                      <button
                        key={t.target}
                        onClick={() => statusMutation.mutate({ id: a.id, status: t.target })}
                        disabled={statusMutation.isPending}
                        className="px-2.5 py-1.5 border border-slate-200 hover:bg-slate-50 text-slate-700 text-[10px] font-bold rounded-lg disabled:opacity-50"
                      >
                        {t.label}
                      </button>
                    ))}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="bg-white border border-slate-200 border-dashed rounded-2xl p-12 text-center text-slate-400 text-xs">
              <Link2 className="w-12 h-12 text-slate-300 mx-auto mb-3 animate-pulse" />
              <span>No assignments match the current filters.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
