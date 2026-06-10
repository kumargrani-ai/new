import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import type {
  LocalityPrice,
  PropertyListing,
  TrendPoint,
  MarketInsight,
  MarketSummary,
  ScraperStatus,
} from "../types";

const api = axios.create({ baseURL: "/api" });

export function useMarketSummary() {
  return useQuery<MarketSummary>({
    queryKey: ["market-summary"],
    queryFn: () => api.get("/market-summary").then((r) => r.data),
    refetchInterval: 5 * 60 * 1000,
  });
}

export function useLocalities() {
  return useQuery<LocalityPrice[]>({
    queryKey: ["localities"],
    queryFn: () => api.get("/localities").then((r) => r.data),
    refetchInterval: 5 * 60 * 1000,
  });
}

export function useListings(locality?: string, propertyType?: string, source?: string) {
  return useQuery<PropertyListing[]>({
    queryKey: ["listings", locality, propertyType, source],
    queryFn: () =>
      api
        .get("/listings", { params: { locality, property_type: propertyType, source, limit: 50 } })
        .then((r) => r.data),
    refetchInterval: 5 * 60 * 1000,
  });
}

export function useTrends(locality?: string) {
  return useQuery<TrendPoint[]>({
    queryKey: ["trends", locality],
    queryFn: () => api.get("/trends", { params: { locality } }).then((r) => r.data),
  });
}

export function useInsights() {
  return useQuery<MarketInsight>({
    queryKey: ["insights"],
    queryFn: () => api.get("/insights").then((r) => r.data),
  });
}

export function useScraperStatus() {
  return useQuery<ScraperStatus[]>({
    queryKey: ["scraper-status"],
    queryFn: () => api.get("/scraper-status").then((r) => r.data),
    refetchInterval: 60 * 1000,
  });
}

export function useRefresh() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post("/refresh").then((r) => r.data),
    onSuccess: () => {
      setTimeout(() => {
        queryClient.invalidateQueries();
      }, 3000);
    },
  });
}
