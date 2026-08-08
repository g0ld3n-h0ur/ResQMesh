import React, { useState } from "react";
import {
  CheckCircle2,
  AlertTriangle,
  Package,
  FileCheck
} from "lucide-react";

interface DeliveryRecord {
  id: string;
  disaster_ref: string;
  item_name: string;
  dispatched_qty: number;
  received_qty: number;
  verified_qty: number;
  discrepancy_qty: number;
  recipient_agency: string;
  status: "PENDING" | "VERIFIED" | "DISCREPANCY_FLAGGED";
  verified_by: string | null;
  evidence_ref: string | null;
  timestamp: string;
}

const INITIAL_DELIVERIES: DeliveryRecord[] = [
  {
    id: "DEL-901",
    disaster_ref: "DIS-2024-001 (Chennai Flood Relief)",
    item_name: "Emergency Medical Kits (Type A)",
    dispatched_qty: 1000,
    received_qty: 980,
    verified_qty: 980,
    discrepancy_qty: 20,
    recipient_agency: "Tambaram General Hospital Zone C",
    status: "DISCREPANCY_FLAGGED",
    verified_by: "Dr. K. Ramanathan (Chief Medical Officer)",
    evidence_ref: "POD_MANIFEST_901_SIGNED.PDF",
    timestamp: "2026-08-08T08:30:00Z",
  },
  {
    id: "DEL-902",
    disaster_ref: "DIS-2024-001 (Chennai Flood Relief)",
    item_name: "Packaged Drinking Water (2L Bottles)",
    dispatched_qty: 5000,
    received_qty: 5000,
    verified_qty: 5000,
    discrepancy_qty: 0,
    recipient_agency: "Velachery Central Shelter",
    status: "VERIFIED",
    verified_by: "S. Priya (Shelter Coordinator)",
    evidence_ref: "POD_MANIFEST_902_STAMPED.PDF",
    timestamp: "2026-08-08T07:15:00Z",
  },
  {
    id: "DEL-903",
    disaster_ref: "DIS-2024-002 (Cuddalore Coastal Storm)",
    item_name: "Tarpaulin & Emergency Tents",
    dispatched_qty: 450,
    received_qty: 450,
    verified_qty: 450,
    discrepancy_qty: 0,
    recipient_agency: "Red Cross Field Unit Cuddalore",
    status: "VERIFIED",
    verified_by: "M. Anbarasan (Red Cross Lead)",
    evidence_ref: "POD_MANIFEST_903_STAMPED.PDF",
    timestamp: "2026-08-08T06:45:00Z",
  },
  {
    id: "DEL-904",
    disaster_ref: "DIS-2024-001 (Chennai Flood Relief)",
    item_name: "High-Calorie Ration Packets",
    dispatched_qty: 2000,
    received_qty: 2000,
    verified_qty: 0,
    discrepancy_qty: 0,
    recipient_agency: "Madipakkam Relief Camp",
    status: "PENDING",
    verified_by: null,
    evidence_ref: null,
    timestamp: "2026-08-08T09:00:00Z",
  },
];

export const ProofOfDelivery: React.FC = () => {
  const [deliveries, setDeliveries] = useState<DeliveryRecord[]>(INITIAL_DELIVERIES);

  const handleVerify = (id: string) => {
    setDeliveries(prev =>
      prev.map(d => {
        if (d.id === id) {
          return {
            ...d,
            status: "VERIFIED",
            verified_qty: d.received_qty,
            verified_by: "Current Authorized User",
            evidence_ref: `POD_MANIFEST_${d.id}_VERIFIED.PDF`,
          };
        }
        return d;
      })
    );
  };

  const totalDispatched = deliveries.reduce((acc, curr) => acc + curr.dispatched_qty, 0);
  const totalVerified = deliveries.reduce((acc, curr) => acc + curr.verified_qty, 0);
  const totalDiscrepancy = deliveries.reduce((acc, curr) => acc + curr.discrepancy_qty, 0);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl text-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-600/30 shrink-0">
            <FileCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-extrabold tracking-tight">Proof of Delivery Verification</h2>
              <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                AUDIT COMPLIANCE
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              End-to-end verification tracking: DISPATCHED → RECEIVED → VERIFIED. Detect discrepancies & lost cargo.
            </p>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex items-center space-x-4">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
            <Package className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-400 font-semibold block">Total Units Dispatched</span>
            <span className="text-2xl font-black text-slate-800">{totalDispatched.toLocaleString()}</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex items-center space-x-4">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-400 font-semibold block">Verified Delivered Units</span>
            <span className="text-2xl font-black text-emerald-600">{totalVerified.toLocaleString()}</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex items-center space-x-4">
          <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-400 font-semibold block">Discrepancy / Loss</span>
            <span className="text-2xl font-black text-rose-600">{totalDiscrepancy.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Main Delivery Table */}
      <div className="bg-white border border-slate-200 rounded-3xl shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-800">Relief Delivery Verification Manifest</h3>
            <p className="text-xs text-slate-400">Matches dispatched warehouse manifests against recipient sign-off receipts.</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-[11px] uppercase font-bold text-slate-500 tracking-wider">
                <th className="py-3 px-4">Delivery Ref</th>
                <th className="py-3 px-4">Disaster Incident</th>
                <th className="py-3 px-4">Item Name</th>
                <th className="py-3 px-4 text-center">Dispatched</th>
                <th className="py-3 px-4 text-center">Received</th>
                <th className="py-3 px-4 text-center">Verified</th>
                <th className="py-3 px-4 text-center">Discrepancy</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {deliveries.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-4 font-mono font-bold text-indigo-600">{item.id}</td>
                  <td className="py-3.5 px-4 text-slate-700 font-medium">{item.disaster_ref}</td>
                  <td className="py-3.5 px-4 font-semibold text-slate-800">{item.item_name}</td>
                  <td className="py-3.5 px-4 text-center font-mono font-bold text-slate-700">{item.dispatched_qty}</td>
                  <td className="py-3.5 px-4 text-center font-mono text-slate-700">{item.received_qty}</td>
                  <td className="py-3.5 px-4 text-center font-mono font-bold text-emerald-600">{item.verified_qty}</td>
                  <td className={`py-3.5 px-4 text-center font-mono font-bold ${item.discrepancy_qty > 0 ? "text-rose-600" : "text-slate-400"}`}>
                    {item.discrepancy_qty}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] uppercase font-bold border ${
                      item.status === "VERIFIED"
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : item.status === "DISCREPANCY_FLAGGED"
                        ? "bg-rose-50 text-rose-700 border-rose-200"
                        : "bg-amber-50 text-amber-700 border-amber-200"
                    }`}>
                      {item.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right space-x-2">
                    {item.status !== "VERIFIED" && (
                      <button
                        onClick={() => handleVerify(item.id)}
                        className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-xs"
                      >
                        Verify Sign-off
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
