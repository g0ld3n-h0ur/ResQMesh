import React from "react";

const CSR_FUNDS = [
  { id: "CSR-2024-A", donor: "Apex Global Foundation", pledged: 500000, deployed: 420000, beneficiaries: 14200, status: "Active" },
  { id: "CSR-2024-B", donor: "MedTech Cares Initiative", pledged: 250000, deployed: 250000, beneficiaries: 8900, status: "Fully Deployed" },
  { id: "CSR-2024-C", donor: "State Relief Syndicate", pledged: 1000000, deployed: 650000, beneficiaries: 28000, status: "Active" },
];

export const CSRTransparency: React.FC = () => {
  return (
    <div className="space-y-4 font-sans text-[#172033]">
      
      {/* Header */}
      <div className="bg-white border border-[#E4E7EC] rounded-md p-3.5 flex items-center justify-between">
        <div>
          <h1 className="text-sm font-bold text-[#172033]">CSR & Corporate Donor Relief Tracking</h1>
          <p className="text-[11px] text-[#667085]">
            Public ledger tracking corporate social responsibility fund deployments and verified beneficiaries.
          </p>
        </div>
        <span className="text-[10px] font-mono text-[#667085]">AUDITED LEDGER</span>
      </div>

      {/* Ledger Table */}
      <div className="bg-white border border-[#E4E7EC] rounded-md overflow-hidden">
        <div className="p-3 border-b border-[#E4E7EC] bg-[#F7F8FA] flex items-center justify-between text-xs">
          <span className="font-bold text-[#172033]">Corporate Fund Grants Ledger</span>
          <span className="text-[10px] text-[#667085]">{CSR_FUNDS.length} Active Grants</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-[#E4E7EC] text-[10px] uppercase font-bold text-[#667085]">
                <th className="py-2 px-3">Grant Ref</th>
                <th className="py-2 px-3">Donor Organization</th>
                <th className="py-2 px-3 text-right">Pledged (USD)</th>
                <th className="py-2 px-3 text-right">Deployed (USD)</th>
                <th className="py-2 px-3 text-right">Deployment %</th>
                <th className="py-2 px-3 text-right">Beneficiaries</th>
                <th className="py-2 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E4E7EC]">
              {CSR_FUNDS.map((fund) => {
                const pct = Math.round((fund.deployed / fund.pledged) * 100);
                return (
                  <tr key={fund.id} className="hover:bg-slate-50">
                    <td className="py-2 px-3 font-mono font-bold text-blue-700">{fund.id}</td>
                    <td className="py-2 px-3 font-semibold text-[#172033]">{fund.donor}</td>
                    <td className="py-2 px-3 text-right font-mono font-medium">${fund.pledged.toLocaleString()}</td>
                    <td className="py-2 px-3 text-right font-mono font-bold text-emerald-700">${fund.deployed.toLocaleString()}</td>
                    <td className="py-2 px-3 text-right font-mono font-bold">{pct}%</td>
                    <td className="py-2 px-3 text-right font-mono font-medium">{fund.beneficiaries.toLocaleString()}</td>
                    <td className="py-2 px-3">
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                        pct === 100
                          ? "bg-slate-100 text-slate-700 border border-slate-200"
                          : "bg-emerald-50 text-emerald-800 border border-emerald-200"
                      }`}>
                        {fund.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
