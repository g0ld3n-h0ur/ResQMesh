import React, { useState } from "react";
import { api } from "../lib/api";

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
    recipient_agency: "Tambaram General Hospital",
    status: "DISCREPANCY_FLAGGED",
  },
  {
    id: "DEL-902",
    disaster_ref: "DIS-2024-001 (Chennai Flood Relief)",
    item_name: "Packaged Water (2L Bottles)",
    dispatched_qty: 5000,
    received_qty: 5000,
    verified_qty: 5000,
    discrepancy_qty: 0,
    recipient_agency: "Velachery Central Shelter",
    status: "VERIFIED",
  },
  {
    id: "DEL-903",
    disaster_ref: "DIS-2024-002 (Cuddalore Storm)",
    item_name: "Emergency Tents & Tarpaulin",
    dispatched_qty: 450,
    received_qty: 450,
    verified_qty: 450,
    discrepancy_qty: 0,
    recipient_agency: "Red Cross Field Unit",
    status: "VERIFIED",
  },
  {
    id: "DEL-904",
    disaster_ref: "DIS-2024-001 (Chennai Flood Relief)",
    item_name: "Ration Packets",
    dispatched_qty: 2000,
    received_qty: 2000,
    verified_qty: 0,
    discrepancy_qty: 0,
    recipient_agency: "Madipakkam Relief Camp",
    status: "PENDING",
  },
];

export const ProofOfDelivery: React.FC = () => {
  const [deliveries, setDeliveries] = useState<DeliveryRecord[]>(INITIAL_DELIVERIES);

  const handleVerify = async (id: string) => {
    const target = deliveries.find(d => d.id === id);
    if (target) {
      try {
        await api.post("/csr/proof-of-delivery", {
          dispatched_quantity: target.dispatched_qty,
          received_quantity: target.received_qty,
          verified_quantity: target.received_qty,
        });
      } catch (err) {
        console.warn("Backend sync failed for proof of delivery", err);
      }
    }
    setDeliveries(prev =>
      prev.map(d => {
        if (d.id === id) {
          return {
            ...d,
            status: "VERIFIED",
            verified_qty: d.received_qty,
            discrepancy_qty: 0,
          };
        }
        return d;
      })
    );
  };

  return (
    <div className="space-y-4 font-sans text-[#172033]">
      
      {/* Header */}
      <div className="bg-white border border-[#E4E7EC] rounded-md p-3.5 flex items-center justify-between">
        <div>
          <h1 className="text-sm font-bold text-[#172033]">Proof of Delivery & Cargo Audit</h1>
          <p className="text-[11px] text-[#667085]">
            End-to-end cargo verification audit matching dispatched manifests against recipient sign-off receipts.
          </p>
        </div>
        <span className="text-[10px] font-mono text-[#667085]">COMPLIANCE MANIFEST</span>
      </div>

      {/* Manifest Table */}
      <div className="bg-white border border-[#E4E7EC] rounded-md overflow-hidden">
        <div className="p-3 border-b border-[#E4E7EC] bg-[#F7F8FA] flex items-center justify-between text-xs">
          <span className="font-bold text-[#172033]">Delivery Manifest Receipts</span>
          <span className="text-[10px] text-[#667085]">{deliveries.length} Records</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-[#E4E7EC] text-[10px] uppercase font-bold text-[#667085]">
                <th className="py-2 px-3">Ref ID</th>
                <th className="py-2 px-3">Disaster Reference</th>
                <th className="py-2 px-3">Item Description</th>
                <th className="py-2 px-3 text-right">Dispatched</th>
                <th className="py-2 px-3 text-right">Received</th>
                <th className="py-2 px-3 text-right">Verified</th>
                <th className="py-2 px-3 text-right">Discrepancy</th>
                <th className="py-2 px-3">Status</th>
                <th className="py-2 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E4E7EC]">
              {deliveries.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50">
                  <td className="py-2 px-3 font-mono font-bold text-blue-700">{item.id}</td>
                  <td className="py-2 px-3 text-[#667085]">{item.disaster_ref}</td>
                  <td className="py-2 px-3 font-medium text-[#172033]">{item.item_name}</td>
                  <td className="py-2 px-3 text-right font-mono font-medium">{item.dispatched_qty.toLocaleString()}</td>
                  <td className="py-2 px-3 text-right font-mono font-medium">{item.received_qty.toLocaleString()}</td>
                  <td className="py-2 px-3 text-right font-mono font-bold text-emerald-700">{item.verified_qty.toLocaleString()}</td>
                  <td className={`py-2 px-3 text-right font-mono font-bold ${item.discrepancy_qty > 0 ? "text-red-600" : "text-[#667085]"}`}>
                    {item.discrepancy_qty}
                  </td>
                  <td className="py-2 px-3">
                    <span className={`px-1.5 py-0.5 rounded text-[9px] uppercase font-bold ${
                      item.status === "VERIFIED"
                        ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                        : item.status === "DISCREPANCY_FLAGGED"
                        ? "bg-red-50 text-red-800 border border-red-200"
                        : "bg-amber-50 text-amber-800 border border-amber-200"
                    }`}>
                      {item.status}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right">
                    {item.status !== "VERIFIED" && (
                      <button
                        onClick={() => handleVerify(item.id)}
                        className="px-2 py-0.5 bg-blue-600 hover:bg-blue-700 text-white text-[10px] font-semibold rounded"
                      >
                        Verify
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
