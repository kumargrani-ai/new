import { Building2, RefreshCw, TrendingUp } from "lucide-react";
import { useRefresh, useMarketSummary } from "../hooks/useRealEstateData";
import clsx from "clsx";

export function Header() {
  const { data: summary } = useMarketSummary();
  const { mutate: refresh, isPending } = useRefresh();

  const lastUpdated = summary?.last_updated
    ? new Date(summary.last_updated).toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "Loading...";

  return (
    <header className="bg-gradient-to-r from-indigo-900 via-indigo-800 to-purple-900 shadow-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          <div className="flex items-center gap-3">
            <div className="bg-white/10 rounded-xl p-2.5 backdrop-blur">
              <Building2 className="text-white w-7 h-7" />
            </div>
            <div>
              <h1 className="text-white text-xl font-bold tracking-tight flex items-center gap-2">
                Hyderabad Real Estate Intelligence
                <TrendingUp className="w-5 h-5 text-green-400" />
              </h1>
              <p className="text-indigo-300 text-xs">
                AI-powered market data from MagicBricks · 99acres · Housing.com · NoBroker · SquareYards
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-indigo-200 text-xs">Last updated</p>
              <p className="text-white text-sm font-medium">{lastUpdated}</p>
            </div>
            <button
              onClick={() => refresh()}
              disabled={isPending}
              className={clsx(
                "flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all",
                isPending
                  ? "bg-white/10 text-white/50 cursor-not-allowed"
                  : "bg-white text-indigo-700 hover:bg-indigo-50 shadow-lg hover:shadow-xl"
              )}
            >
              <RefreshCw className={clsx("w-4 h-4", isPending && "animate-spin")} />
              {isPending ? "Refreshing..." : "Refresh Data"}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
