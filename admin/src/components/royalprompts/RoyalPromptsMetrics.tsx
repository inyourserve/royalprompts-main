"use client";
import React, { useState, useEffect } from "react";
import Badge from "../ui/badge/Badge";
import { ArrowUpIcon, BoxIconLine, GroupIcon, FileIcon, FolderIcon } from "@/icons";
import { dashboardApi } from "@/services";

interface MetricsData {
  total_prompts: number;
  total_categories: number;
  total_devices: number;
  active_devices_today: number;
  total_favorites: number;
  total_unlocks: number;
}

export const RoyalPromptsMetrics = () => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const data = await dashboardApi.getDashboardStats();
        setMetrics(data);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch metrics:", err);
        setError(err instanceof Error ? err.message : "Failed to load metrics");
        
        // Fallback to mock data if API fails
        setMetrics({
          total_prompts: 0,
          total_categories: 4, // Static categories
          total_devices: 0,
          active_devices_today: 0,
          total_favorites: 0,
          total_unlocks: 0
        });
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);


  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:gap-6 lg:grid-cols-4">
        {[...Array(4)].map((_, index) => (
          <div key={index} className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] md:p-6">
            <div className="animate-pulse">
              <div className="w-12 h-12 bg-gray-200 rounded-xl dark:bg-gray-700"></div>
              <div className="mt-5">
                <div className="h-4 bg-gray-200 rounded dark:bg-gray-700 w-24"></div>
                <div className="h-6 bg-gray-200 rounded dark:bg-gray-700 w-16 mt-2"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-5 dark:border-red-800 dark:bg-red-900/20 md:p-6">
        <p className="text-red-600 dark:text-red-400">Failed to load metrics: {error}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:gap-6 lg:grid-cols-4">
      {/* Total Prompts */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] md:p-6">
        <div className="flex items-center justify-center w-12 h-12 bg-gray-100 rounded-xl dark:bg-gray-800">
          <FileIcon className="text-gray-800 size-6 dark:text-white/90" />
        </div>

        <div className="flex items-end justify-between mt-5">
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Total Prompts
            </span>
            <h4 className="mt-2 font-bold text-gray-800 text-title-sm dark:text-white/90">
              {metrics?.total_prompts?.toLocaleString() || "0"}
            </h4>
          </div>
          <Badge color="success">
            <ArrowUpIcon />
            +0%
          </Badge>
        </div>
      </div>

      {/* Total Categories */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] md:p-6">
        <div className="flex items-center justify-center w-12 h-12 bg-gray-100 rounded-xl dark:bg-gray-800">
          <FolderIcon className="text-gray-800 size-6 dark:text-white/90" />
        </div>
        <div className="flex items-end justify-between mt-5">
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Categories
            </span>
            <h4 className="mt-2 font-bold text-gray-800 text-title-sm dark:text-white/90">
              {metrics?.total_categories?.toLocaleString() || "4"}
            </h4>
          </div>
          <Badge color="primary">
            Static
          </Badge>
        </div>
      </div>

      {/* Active Users */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] md:p-6">
        <div className="flex items-center justify-center w-12 h-12 bg-gray-100 rounded-xl dark:bg-gray-800">
          <GroupIcon className="text-gray-800 size-6 dark:text-white/90" />
        </div>
        <div className="flex items-end justify-between mt-5">
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Active Devices
            </span>
            <h4 className="mt-2 font-bold text-gray-800 text-title-sm dark:text-white/90">
              {metrics?.active_devices_today?.toLocaleString() || "0"}
            </h4>
          </div>
          <Badge color="success">
            <ArrowUpIcon />
            Today
          </Badge>
        </div>
      </div>

      {/* Trending Prompts */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] md:p-6">
        <div className="flex items-center justify-center w-12 h-12 bg-gray-100 rounded-xl dark:bg-gray-800">
          <BoxIconLine className="text-gray-800 size-6 dark:text-white/90" />
        </div>
        <div className="flex items-end justify-between mt-5">
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Total Unlocks
            </span>
            <h4 className="mt-2 font-bold text-gray-800 text-title-sm dark:text-white/90">
              {metrics?.total_unlocks?.toLocaleString() || "0"}
            </h4>
          </div>
          <Badge color="success">
            <ArrowUpIcon />
            +0%
          </Badge>
        </div>
      </div>
    </div>
  );
};
