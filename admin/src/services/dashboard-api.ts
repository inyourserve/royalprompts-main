/**
 * Dashboard API service
 */

import { BaseApiService } from './base-api';
import { DashboardStats, ChartData, RecentPromptsResponse } from '@/types';

export class DashboardApiService extends BaseApiService {
  async getDashboardStats(): Promise<DashboardStats> {
    return this.request<DashboardStats>('/api/admin/dashboard');
  }

  async getChartData(): Promise<ChartData> {
    return this.request<ChartData>('/api/admin/dashboard/chart-data');
  }

  async getRecentPrompts(): Promise<RecentPromptsResponse> {
    // Get recent prompts for dashboard by calling prompts API
    const response = await this.request<any>('/api/admin/prompts?page=1&limit=5');
    return { prompts: response.items || [] };
  }
}

export const dashboardApi = new DashboardApiService();
