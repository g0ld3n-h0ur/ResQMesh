import React from "react";
import {
  Building2,
  Users,
  DollarSign,
  Award
} from "lucide-react";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from "recharts";

interface CSRProgram {
  id: string;
  donor_org: string;
  program_name: string;
  pledged_amount_inr: number;
  deployed_amount_inr: number;
  remaining_amount_inr: number;
  beneficiaries_served: number;
  relief_units_delivered: number;
  locations_served: string[];
  status: "ACTIVE" | "COMPLETED";
}

const CSR_PROGRAMS: CSRProgram[] = [
  {
    id: "CSR-2024-01",
    donor_org: "Tata Sustainability Group",
    program_name: "Chennai Flood Relief & Clean Water Mission",
    pledged_amount_inr: 25000000,
    deployed_amount_inr: 18500000,
    remaining_amount_inr: 6500000,
    beneficiaries_served: 42000,
    relief_units_delivered: 12500,
    locations_served: ["Velachery", "Madipakkam", "Tambaram"],
    status: "ACTIVE",
  },
  {
    id: "CSR-2024-02",
    donor_org: "Infosys Foundation",
    program_name: "Emergency Medical Supply & ICU Support",
    pledged_amount_inr: 15000000,
    deployed_amount_inr: 15000000,
    remaining_amount_inr: 0,
    beneficiaries_served: 18500,
    relief_units_delivered: 4500,
    locations_served: ["Cuddalore", "Nagapattinam"],
    status: "COMPLETED",
  },
  {
    id: "CSR-2024-03",
    donor_org: "Reliance Foundation",
    program_name: "Disaster Shelter & Temporary Housing",
    pledged_amount_inr: 30000000,
    deployed_amount_inr: 21000000,
    remaining_amount_inr: 9000000,
    beneficiaries_served: 55000,
    relief_units_delivered: 8200,
    locations_served: ["Chennai South", "Chengalpattu"],
    status: "ACTIVE",
  },
];

const PIE_COLORS = ["#4f46e5", "#10b981", "#f59e0b", "#ec4899"];

export const CSRTransparency: React.FC = () => {
  const totalPledged = CSR_PROGRAMS.reduce((acc, curr) => acc + curr.pledged_amount_inr, 0);
  const totalDeployed = CSR_PROGRAMS.reduce((acc, curr) => acc + curr.deployed_amount_inr, 0);
  const totalBeneficiaries = CSR_PROGRAMS.reduce((acc, curr) => acc + curr.beneficiaries_served, 0);

  const pieData = CSR_PROGRAMS.map((p) => ({
    name: p.donor_org,
    value: p.deployed_amount_inr,
  }));

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl text-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-600/30 shrink-0">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-extrabold tracking-tight">CSR Relief Tracking & Donor Transparency</h2>
              <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                AUDITED PUBLIC LEDGER
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Transparent corporate social responsibility allocation tracking with verified delivery metrics and public impact proof.
            </p>
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex items-center space-x-4">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
            <DollarSign className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-400 font-semibold block">Total CSR Funds Deployed</span>
            <span className="text-2xl font-black text-slate-800">
              ₹{(totalDeployed / 10000000).toFixed(2)} Cr
            </span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex items-center space-x-4">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-400 font-semibold block">Verified Beneficiaries</span>
            <span className="text-2xl font-black text-emerald-600">{totalBeneficiaries.toLocaleString()}</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex items-center space-x-4">
          <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-400 font-semibold block">Fund Utilization Rate</span>
            <span className="text-2xl font-black text-purple-600">
              {((totalDeployed / totalPledged) * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* CSR Programs Table */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-4">
          <h3 className="text-base font-bold text-slate-800 border-b border-slate-100 pb-3">
            Active Corporate CSR Disaster Relief Programs
          </h3>

          <div className="space-y-4">
            {CSR_PROGRAMS.map((program) => {
              const pct = Math.round((program.deployed_amount_inr / program.pledged_amount_inr) * 100);
              return (
                <div key={program.id} className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-[10px] font-mono text-slate-400">{program.id} • {program.donor_org}</span>
                      <h4 className="font-bold text-slate-800 text-sm mt-0.5">{program.program_name}</h4>
                    </div>
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                      program.status === "COMPLETED"
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : "bg-indigo-50 text-indigo-700 border-indigo-200"
                    }`}>
                      {program.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-xs pt-1">
                    <div>
                      <span className="text-slate-400 text-[10px] block">Pledged</span>
                      <span className="font-semibold text-slate-800">₹{(program.pledged_amount_inr / 100000).toFixed(1)} L</span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] block">Deployed</span>
                      <span className="font-semibold text-emerald-600">₹{(program.deployed_amount_inr / 100000).toFixed(1)} L</span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] block">Beneficiaries</span>
                      <span className="font-semibold text-indigo-600">{program.beneficiaries_served.toLocaleString()}</span>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] text-slate-500 font-medium">
                      <span>Fund Deployment</span>
                      <span>{pct}%</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                      <div className="bg-indigo-600 h-2 rounded-full" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* CSR Breakdown Chart */}
        <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm flex flex-col justify-between space-y-4">
          <h3 className="text-base font-bold text-slate-800 border-b border-slate-100 pb-3">
            CSR Deployment Breakdown
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: unknown) => typeof value === "number" ? `₹${(value / 100000).toFixed(1)} Lakhs` : String(value ?? "")} />
                <Legend wrapperStyle={{ fontSize: "11px" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
