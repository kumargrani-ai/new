import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, LabelList,
} from "recharts";
import { useLocalities } from "../hooks/useRealEstateData";
import clsx from "clsx";

const DEMAND_COLORS: Record<string, string> = {
  High: "#6366f1",
  Medium: "#10b981",
  Low: "#f59e0b",
};

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; payload: { name: string; demand_level: string; listing_count: number; avg_price_2bhk_lakhs?: number; avg_price_3bhk_lakhs?: number } }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const fmt = (n: number) => new Intl.NumberFormat("en-IN").format(Math.round(n));
  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-lg p-4 text-sm">
      <p className="font-bold text-gray-900 mb-2">{d.name}</p>
      <p className="text-indigo-600 font-semibold">₹{fmt(payload[0].value)}/sqft</p>
      {d.avg_price_2bhk_lakhs && (
        <p className="text-gray-600 mt-1">2BHK avg: ₹{d.avg_price_2bhk_lakhs.toFixed(1)}L</p>
      )}
      {d.avg_price_3bhk_lakhs && (
        <p className="text-gray-600">3BHK avg: ₹{d.avg_price_3bhk_lakhs.toFixed(1)}L</p>
      )}
      <p className="text-gray-500 mt-1">{d.listing_count} listings</p>
      <span
        className={clsx(
          "inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-medium text-white",
          d.demand_level === "High" ? "bg-indigo-500" : d.demand_level === "Medium" ? "bg-emerald-500" : "bg-amber-500"
        )}
      >
        {d.demand_level} Demand
      </span>
    </div>
  );
}

export function PriceByLocality() {
  const { data: localities, isLoading } = useLocalities();

  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <div className="h-6 bg-gray-200 rounded w-48 mb-6 animate-pulse" />
        <div className="h-72 bg-gray-100 rounded-xl animate-pulse" />
      </div>
    );
  }

  const data = (localities || [])
    .slice(0, 14)
    .sort((a, b) => b.avg_price_per_sqft - a.avg_price_per_sqft);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Price by Locality</h2>
          <p className="text-sm text-gray-500 mt-0.5">Avg. price per sq.ft (INR)</p>
        </div>
        <div className="flex gap-3 text-xs">
          {Object.entries(DEMAND_COLORS).map(([level, color]) => (
            <span key={level} className="flex items-center gap-1.5 text-gray-600">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
              {level}
            </span>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} margin={{ top: 16, right: 16, left: 0, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11, fill: "#6b7280" }}
            angle={-35}
            textAnchor="end"
            interval={0}
            height={70}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#6b7280" }}
            tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
            width={52}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f0f0ff" }} />
          <Bar dataKey="avg_price_per_sqft" radius={[6, 6, 0, 0]} maxBarSize={40}>
            {data.map((entry, i) => (
              <Cell
                key={i}
                fill={DEMAND_COLORS[entry.demand_level] ?? "#6366f1"}
                fillOpacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
