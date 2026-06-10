import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Header } from "./components/Header";
import { MetricCards } from "./components/MetricCards";
import { PriceByLocality } from "./components/PriceByLocality";
import { PriceTrends } from "./components/PriceTrends";
import { PropertyTypeChart } from "./components/PropertyTypeChart";
import { InsightPanel } from "./components/InsightPanel";
import { RecentListings } from "./components/RecentListings";
import { DataSourceStatus } from "./components/DataSourceStatus";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 2 * 60 * 1000,
    },
  },
});

function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* KPI Cards */}
        <MetricCards />

        {/* Charts row */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <PriceByLocality />
          <PriceTrends />
        </div>

        {/* Property type + AI Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <PropertyTypeChart />
          <div className="lg:col-span-2">
            <InsightPanel />
          </div>
        </div>

        {/* Listings table */}
        <RecentListings />

        {/* Data sources */}
        <DataSourceStatus />
      </main>

      <footer className="border-t border-gray-200 bg-white mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex items-center justify-between text-sm text-gray-500">
          <p>Hyderabad Real Estate Intelligence — AI Agent Dashboard</p>
          <p>Data from MagicBricks · 99acres · Housing.com · NoBroker · Square Yards</p>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  );
}
