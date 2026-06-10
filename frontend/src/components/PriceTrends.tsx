import { useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { useTrends } from "../hooks/useRealEstateData";

const LOCALITIES = [
  "Gachibowli", "Hitech City", "Kondapur", "Banjara Hills",
  "Kokapet", "Kukatpally",
];

const LINE_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

export function PriceTrends() {
  const [selected, setSelected] = useState<string[]>(LOCALITIES.slice(0, 4));
  const { data: trends, isLoading } = useTrends();

  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <div className="h-6 bg-gray-200 rounded w-48 mb-6 animate-pulse" />
        <div className="h-72 bg-gray-100 rounded-xl animate-pulse" />
      </div>
    );
  }

  // Pivot: month → { month, [locality]: price }
  const monthMap: Record<string, Record<string, number>> = {};
  (trends || []).forEach(({ month, locality, avg_price_per_sqft }) => {
    if (!monthMap[month]) monthMap[month] = { month };
    monthMap[month][locality] = avg_price_per_sqft;
  });
  const chartData = Object.values(monthMap).sort((a, b) =>
    String(a.month).localeCompare(String(b.month))
  );

  const allLocalities = [...new Set((trends || []).map((t) => t.locality))];

  const toggle = (loc: string) =>
    setSelected((prev) =>
      prev.includes(loc) ? prev.filter((l) => l !== loc) : [...prev, loc]
    );

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-gray-900">12-Month Price Trends</h2>
          <p className="text-sm text-gray-500 mt-0.5">₹/sqft over time by locality</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-5">
        {allLocalities.map((loc, i) => (
          <button
            key={loc}
            onClick={() => toggle(loc)}
            className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-all ${
              selected.includes(loc)
                ? "text-white border-transparent"
                : "text-gray-500 border-gray-200 bg-white hover:border-gray-400"
            }`}
            style={selected.includes(loc) ? { backgroundColor: LINE_COLORS[i % LINE_COLORS.length] } : {}}
          >
            {loc}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 5, right: 16, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis
            dataKey="month"
            tick={{ fontSize: 11, fill: "#6b7280" }}
            tickFormatter={(v) => {
              const [year, month] = String(v).split("-");
              const d = new Date(Number(year), Number(month) - 1);
              return d.toLocaleDateString("en-IN", { month: "short", year: "2-digit" });
            }}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#6b7280" }}
            tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
            width={52}
          />
          <Tooltip
            formatter={(val: number, name: string) => [`₹${val.toLocaleString("en-IN")}/sqft`, name]}
            labelFormatter={(label) => {
              const [year, month] = String(label).split("-");
              return new Date(Number(year), Number(month) - 1).toLocaleDateString("en-IN", {
                month: "long",
                year: "numeric",
              });
            }}
          />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          {allLocalities
            .filter((loc) => selected.includes(loc))
            .map((loc, i) => (
              <Line
                key={loc}
                type="monotone"
                dataKey={loc}
                stroke={LINE_COLORS[allLocalities.indexOf(loc) % LINE_COLORS.length]}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 5 }}
              />
            ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
