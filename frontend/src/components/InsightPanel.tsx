import { Sparkles, TrendingUp } from "lucide-react";
import { useInsights } from "../hooks/useRealEstateData";

export function InsightPanel() {
  const { data: insight, isLoading } = useInsights();

  if (isLoading) {
    return (
      <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl border border-indigo-100 p-6">
        <div className="h-6 bg-indigo-200 rounded w-56 mb-4 animate-pulse" />
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-4 bg-indigo-100 rounded mb-2 animate-pulse" style={{ width: `${90 - i * 10}%` }} />
        ))}
      </div>
    );
  }

  if (!insight) return null;

  // Convert markdown-like bold to HTML
  const paragraphs = insight.insight_text.split("\n\n").filter(Boolean);

  return (
    <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl border border-indigo-100 p-6">
      <div className="flex items-center gap-2 mb-4">
        <div className="bg-indigo-600 rounded-lg p-1.5">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-gray-900">AI Market Insights</h2>
          <p className="text-xs text-gray-500">
            Powered by Claude ·{" "}
            {insight.generated_at
              ? new Date(insight.generated_at).toLocaleString("en-IN", {
                  day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
                })
              : "Latest analysis"}
          </p>
        </div>
        <div className="ml-auto flex items-center gap-1.5 bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-semibold">
          <TrendingUp className="w-4 h-4" />
          +{insight.yoy_change_pct.toFixed(1)}% YoY
        </div>
      </div>

      <div className="space-y-4 text-sm text-gray-700 leading-relaxed">
        {paragraphs.map((para, i) => {
          if (para.startsWith("**")) {
            const titleEnd = para.indexOf("**", 2);
            const title = para.substring(2, titleEnd);
            const rest = para.substring(titleEnd + 2).trim();
            return (
              <div key={i}>
                <h3 className="font-bold text-indigo-800 mb-1">{title}</h3>
                {rest && <p>{rest}</p>}
              </div>
            );
          }
          return <p key={i}>{para}</p>;
        })}
      </div>

      <div className="mt-5 pt-4 border-t border-indigo-100 grid grid-cols-3 gap-4">
        <div className="text-center">
          <p className="text-xs text-gray-500">City Avg</p>
          <p className="text-base font-bold text-indigo-700">
            ₹{new Intl.NumberFormat("en-IN").format(Math.round(insight.avg_price_per_sqft))}/sqft
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">Total Listings</p>
          <p className="text-base font-bold text-indigo-700">
            {new Intl.NumberFormat("en-IN").format(insight.total_listings)}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">Top Market</p>
          <p className="text-base font-bold text-indigo-700">{insight.hottest_locality}</p>
        </div>
      </div>
    </div>
  );
}
