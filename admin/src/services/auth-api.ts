/**
 * Authentication API service
 */

import { BaseApiService } from './base-api';
import { LoginRequest, LoginResponse, AdminUser } from '@/types';

export class AuthApiService extends BaseApiService {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    return this.request<LoginResponse>('/api/admin/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async getCurrentAdmin(): Promise<AdminUser> {
    return this.request<AdminUser>('/api/admin/auth/me');
  }

  async logout(): Promise<void> {
    // In a real app, you might want to call a logout endpoint
    // For now, we just clear the local storage in the auth context
  }
}

export const authApi = new AuthApiService();
