import { useState } from "react";
import { ExternalLink, Filter } from "lucide-react";
import { useListings } from "../hooks/useRealEstateData";
import clsx from "clsx";

const SOURCE_COLORS: Record<string, string> = {
  MagicBricks: "bg-orange-100 text-orange-700",
  "99acres": "bg-blue-100 text-blue-700",
  "Housing.com": "bg-green-100 text-green-700",
  NoBroker: "bg-purple-100 text-purple-700",
  "Square Yards": "bg-pink-100 text-pink-700",
};

const TYPE_ICONS: Record<string, string> = {
  Apartment: "🏢",
  Villa: "🏡",
  Plot: "🏞️",
  "Independent House": "🏠",
  Commercial: "🏗️",
};

export function RecentListings() {
  const [selectedSource, setSelectedSource] = useState<string | undefined>();
  const [selectedType, setSelectedType] = useState<string | undefined>();
  const { data: listings, isLoading } = useListings(undefined, selectedType, selectedSource);

  const sources = ["MagicBricks", "99acres", "Housing.com", "NoBroker", "Square Yards"];
  const types = ["Apartment", "Villa", "Plot", "Independent House"];

  const fmt = (n: number) =>
    new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(n);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Recent Listings</h2>
          <p className="text-sm text-gray-500 mt-0.5">{listings?.length ?? 0} properties shown</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <Filter className="w-3.5 h-3.5" />
          </div>
          {sources.map((s) => (
            <button
              key={s}
              onClick={() => setSelectedSource(selectedSource === s ? undefined : s)}
              className={clsx(
                "px-2.5 py-1 rounded-full text-xs font-medium border transition-all",
                selectedSource === s
                  ? SOURCE_COLORS[s] + " border-transparent"
                  : "text-gray-500 border-gray-200 hover:border-gray-400"
              )}
            >
              {s}
            </button>
          ))}
          {types.map((t) => (
            <button
              key={t}
              onClick={() => setSelectedType(selectedType === t ? undefined : t)}
              className={clsx(
                "px-2.5 py-1 rounded-full text-xs font-medium border transition-all",
                selectedType === t
                  ? "bg-indigo-100 text-indigo-700 border-transparent"
                  : "text-gray-500 border-gray-200 hover:border-gray-400"
              )}
            >
              {TYPE_ICONS[t]} {t}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide py-3 pr-4">Property</th>
              <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide py-3 pr-4">Locality</th>
              <th className="text-right text-xs font-semibold text-gray-500 uppercase tracking-wide py-3 pr-4">Price</th>
              <th className="text-right text-xs font-semibold text-gray-500 uppercase tracking-wide py-3 pr-4">Area</th>
              <th className="text-right text-xs font-semibold text-gray-500 uppercase tracking-wide py-3 pr-4">₹/sqft</th>
              <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide py-3 pr-4">Source</th>
              <th className="py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              [...Array(8)].map((_, i) => (
                <tr key={i} className="animate-pulse">
                  {[...Array(7)].map((_, j) => (
                    <td key={j} className="py-3 pr-4">
                      <div className="h-4 bg-gray-100 rounded w-full" />
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              (listings || []).slice(0, 20).map((listing) => (
                <tr key={listing.id} className="hover:bg-gray-50 transition-colors group">
                  <td className="py-3 pr-4">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{TYPE_ICONS[listing.property_type] ?? "🏠"}</span>
                      <div>
                        <p className="text-sm font-medium text-gray-900 line-clamp-1 max-w-xs">
                          {listing.title}
                        </p>
                        {listing.bedrooms && (
                          <p className="text-xs text-gray-400">{listing.bedrooms} BHK · {listing.furnishing || "Unfurnished"}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="py-3 pr-4">
                    <span className="text-sm text-gray-700">{listing.locality}</span>
                  </td>
                  <td className="py-3 pr-4 text-right">
                    <span className="text-sm font-semibold text-gray-900">
                      ₹{listing.price_lakhs >= 100
                        ? `${(listing.price_lakhs / 100).toFixed(2)} Cr`
                        : `${listing.price_lakhs.toFixed(1)} L`}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-right text-sm text-gray-600">
                    {fmt(listing.area_sqft)} sqft
                  </td>
                  <td className="py-3 pr-4 text-right">
                    <span className="text-sm font-medium text-indigo-600">
                      ₹{fmt(listing.price_per_sqft)}
                    </span>
                  </td>
                  <td className="py-3 pr-4">
                    <span className={clsx("px-2 py-0.5 rounded-full text-xs font-medium", SOURCE_COLORS[listing.source] ?? "bg-gray-100 text-gray-600")}>
                      {listing.source}
                    </span>
                  </td>
                  <td className="py-3">
                    {listing.source_url && (
                      <a
                        href={listing.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <ExternalLink className="w-4 h-4 text-gray-400 hover:text-indigo-500" />
                      </a>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
