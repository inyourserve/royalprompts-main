/**
 * Settings API service
 */

import { BaseApiService } from './base-api';

export interface AppSettings {
  id?: string;
  app_name: string;
  description: string;
  about_text?: string;
  how_to_use?: string;
  contact_email: string;
  created_at?: string;
  updated_at?: string;
}

export interface AppSettingsUpdate {
  app_name?: string;
  description?: string;
  about_text?: string;
  how_to_use?: string;
  contact_email?: string;
}

export class SettingsApiService extends BaseApiService {
  async getAppSettings(): Promise<AppSettings> {
    return this.request<AppSettings>('/api/admin/settings/app');
  }

  async updateAppSettings(settings: AppSettingsUpdate): Promise<AppSettings> {
    return this.request<AppSettings>('/api/admin/settings/app', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  async createAppSettings(settings: Omit<AppSettings, 'id' | 'created_at' | 'updated_at'>): Promise<AppSettings> {
    return this.request<AppSettings>('/api/admin/settings/app', {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  }

  async resetAppSettings(): Promise<AppSettings> {
    return this.request<AppSettings>('/api/admin/settings/app/reset', {
      method: 'POST',
    });
  }
}

export const settingsApi = new SettingsApiService();
