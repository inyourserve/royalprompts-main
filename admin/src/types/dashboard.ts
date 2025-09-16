/**
 * Dashboard related types
 */

export interface DashboardStats {
  total_prompts: number;
  total_categories: number;
  total_devices: number;
  active_devices_today: number;
  total_favorites: number;
  total_unlocks: number;
  prompts_by_category?: Record<string, number>;
  recent_activity?: any[];
}

export interface MetricsData {
  total_prompts: number;
  total_categories: number;
  total_devices: number;
  active_devices_today: number;
  total_favorites: number;
  total_unlocks: number;
}

export interface ChartData {
  prompts_added: number[];
  trending_prompts: number[];
  totals: {
    total_prompts_added: number;
    total_trending: number;
  };
}

export interface RecentPromptsResponse {
  prompts: any[];
}
