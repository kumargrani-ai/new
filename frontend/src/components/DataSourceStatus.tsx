import { CheckCircle2, XCircle, AlertCircle, Clock } from "lucide-react";
import { useScraperStatus } from "../hooks/useRealEstateData";
import clsx from "clsx";

const SOURCE_URLS: Record<string, string> = {
  MagicBricks: "https://www.magicbricks.com",
  "99acres": "https://www.99acres.com",
  "Housing.com": "https://housing.com",
  NoBroker: "https://www.nobroker.in",
  "Square Yards": "https://www.squareyards.com",
};

export function DataSourceStatus() {
  const { data: statuses, isLoading } = useScraperStatus();

  const allSources = ["MagicBricks", "99acres", "Housing.com", "NoBroker", "Square Yards"];

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-bold text-gray-900 mb-4">Data Sources</h2>
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
        {allSources.map((source) => {
          const status = statuses?.find((s) => s.source === source);
          const ok = status?.status === "success";
          const failed = status?.status === "failed";

          return (
            <a
              key={source}
              href={SOURCE_URLS[source]}
              target="_blank"
              rel="noopener noreferrer"
              className={clsx(
                "flex flex-col items-center p-4 rounded-xl border transition-all hover:shadow-md",
                ok
                  ? "border-green-200 bg-green-50"
                  : failed
                  ? "border-red-200 bg-red-50"
                  : isLoading
                  ? "border-gray-100 bg-gray-50 animate-pulse"
                  : "border-amber-200 bg-amber-50"
              )}
            >
              {isLoading ? (
                <Clock className="w-6 h-6 text-gray-400 mb-2" />
              ) : ok ? (
                <CheckCircle2 className="w-6 h-6 text-green-600 mb-2" />
              ) : failed ? (
                <XCircle className="w-6 h-6 text-red-500 mb-2" />
              ) : (
                <AlertCircle className="w-6 h-6 text-amber-500 mb-2" />
              )}
              <p className="text-xs font-semibold text-gray-800 text-center">{source}</p>
              {status && (
                <p className="text-xs text-gray-500 mt-1">
                  {status.listings_scraped} listings
                </p>
              )}
              {status?.run_at && (
                <p className="text-xs text-gray-400 mt-0.5">
                  {new Date(status.run_at).toLocaleTimeString("en-IN", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              )}
            </a>
          );
        })}
      </div>
    </div>
  );
}
