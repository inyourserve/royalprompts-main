/**
 * Users API service (Device Users)
 */

import { BaseApiService } from './base-api';

export interface DeviceUser {
  id: string;
  device_id: string;
  device_type: 'android' | 'ios' | 'web';
  device_model?: string;
  os_version?: string;
  app_version?: string;
  user_type: 'anonymous';
  is_active: boolean;
  is_blocked: boolean;
  first_seen: string;
  last_seen: string;
  total_requests: number;
  daily_requests: number;
  country?: string;
  ip_address?: string;
  user_agent?: string;
  favorite_prompts: string[];
  unlocked_prompts: string[];
  total_favorites: number;
}

export interface DeviceUserUpdate {
  is_active?: boolean;
  is_blocked?: boolean;
}

export interface DeviceUserListResponse {
  items: DeviceUser[];
  total: number;
  page: number;
  limit: number;
}

export interface DeviceUserStats {
  total_users: number;
  active_users: number;
  blocked_users: number;
  android_users: number;
  ios_users: number;
  web_users: number;
  new_users_today: number;
  new_users_this_week: number;
  new_users_this_month: number;
  most_active_country?: string;
  total_requests_today: number;
  total_requests_this_week: number;
}

export class UsersApiService extends BaseApiService {
  async getUsers(
    page: number = 1,
    limit: number = 20,
    search?: string,
    deviceType?: string,
    isActive?: boolean,
    isBlocked?: boolean
  ): Promise<DeviceUserListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });

    if (search) params.append('search', search);
    if (deviceType) params.append('device_type', deviceType);
    if (isActive !== undefined) params.append('is_active', isActive.toString());
    if (isBlocked !== undefined) params.append('is_blocked', isBlocked.toString());

    return this.request<DeviceUserListResponse>(`/api/admin/users/?${params.toString()}`);
  }

  async getUserById(id: string): Promise<DeviceUser> {
    return this.request<DeviceUser>(`/api/admin/users/${id}`);
  }

  async updateUser(id: string, user: DeviceUserUpdate): Promise<DeviceUser> {
    return this.request<DeviceUser>(`/api/admin/users/${id}`, {
      method: 'PUT',
      body: JSON.stringify(user),
    });
  }

  async deleteUser(id: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/admin/users/${id}`, {
      method: 'DELETE',
    });
  }

  async blockUser(id: string): Promise<DeviceUser> {
    return this.request<DeviceUser>(`/api/admin/users/${id}/block`, {
      method: 'POST',
    });
  }

  async unblockUser(id: string): Promise<DeviceUser> {
    return this.request<DeviceUser>(`/api/admin/users/${id}/unblock`, {
      method: 'POST',
    });
  }

  async getUserStats(): Promise<DeviceUserStats> {
    return this.request<DeviceUserStats>('/api/admin/users/stats');
  }
}

export const usersApi = new UsersApiService();
