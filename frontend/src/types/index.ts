export interface LocalityPrice {
  name: string;
  avg_price_per_sqft: number;
  min_price_per_sqft: number | null;
  max_price_per_sqft: number | null;
  avg_price_2bhk_lakhs: number | null;
  avg_price_3bhk_lakhs: number | null;
  yoy_change_pct: number;
  demand_level: "High" | "Medium" | "Low";
  listing_count: number;
  scraped_at: string | null;
}

export interface PropertyListing {
  id: number;
  title: string;
  locality: string;
  price_lakhs: number;
  area_sqft: number;
  price_per_sqft: number;
  bedrooms: number | null;
  property_type: string;
  source: string;
  source_url: string | null;
  furnishing: string | null;
  scraped_at: string | null;
}

export interface TrendPoint {
  month: string;
  avg_price_per_sqft: number;
  locality: string;
}

export interface MarketInsight {
  insight_text: string;
  market_summary: string;
  avg_price_per_sqft: number;
  total_listings: number;
  hottest_locality: string;
  yoy_change_pct: number;
  generated_at: string | null;
}

export interface MarketSummary {
  avg_price_per_sqft: number;
  total_listings: number;
  hottest_locality: string;
  yoy_change_pct: number;
  last_updated: string | null;
  localities_tracked: number;
}

export interface ScraperStatus {
  source: string;
  status: "success" | "failed" | "partial";
  listings_scraped: number;
  error_message: string | null;
  run_at: string | null;
}
