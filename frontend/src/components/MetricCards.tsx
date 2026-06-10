import { TrendingUp, TrendingDown, Home, MapPin, BarChart3, Layers } from "lucide-react";
import { useMarketSummary } from "../hooks/useRealEstateData";
import clsx from "clsx";

interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: number;
  colorClass: string;
  bgClass: string;
}

function MetricCard({ title, value, subtitle, icon, trend, colorClass, bgClass }: MetricCardProps) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className={clsx("rounded-xl p-3", bgClass)}>{icon}</div>
        {trend !== undefined && (
          <div
            className={clsx(
              "flex items-center gap-1 text-sm font-semibold px-2.5 py-1 rounded-full",
              trend >= 0 ? "bg-green-50 text-green-700" : "bg-red-50 text-red-600"
            )}
          >
            {trend >= 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
            {Math.abs(trend).toFixed(1)}%
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-sm text-gray-500 font-medium">{title}</p>
        <p className={clsx("text-2xl font-bold mt-1", colorClass)}>{value}</p>
        {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
      </div>
    </div>
  );
}

export function MetricCards() {
  const { data: summary, isLoading } = useMarketSummary();

  if (isLoading || !summary) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 animate-pulse">
            <div className="w-12 h-12 bg-gray-200 rounded-xl mb-4" />
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
            <div className="h-8 bg-gray-200 rounded w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  const fmt = (n: number) =>
    new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(n);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricCard
        title="Avg. Price per Sq.ft"
        value={`₹${fmt(summary.avg_price_per_sqft)}`}
        subtitle="Hyderabad overall average"
        icon={<BarChart3 className="w-6 h-6 text-indigo-600" />}
        trend={summary.yoy_change_pct}
        colorClass="text-indigo-700"
        bgClass="bg-indigo-50"
      />
      <MetricCard
        title="Active Listings"
        value={fmt(summary.total_listings)}
        subtitle="Across all sources"
        icon={<Home className="w-6 h-6 text-emerald-600" />}
        colorClass="text-emerald-700"
        bgClass="bg-emerald-50"
      />
      <MetricCard
        title="Hottest Locality"
        value={summary.hottest_locality}
        subtitle="Highest YoY growth"
        icon={<MapPin className="w-6 h-6 text-rose-600" />}
        colorClass="text-rose-700"
        bgClass="bg-rose-50"
      />
      <MetricCard
        title="Localities Tracked"
        value={String(summary.localities_tracked)}
        subtitle="Active micro-markets"
        icon={<Layers className="w-6 h-6 text-amber-600" />}
        trend={summary.yoy_change_pct}
        colorClass="text-amber-700"
        bgClass="bg-amber-50"
      />
    </div>
  );
}
