/**
 * Authentication related types
 */

import { BaseEntity } from './common';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AdminUser extends BaseEntity {
  email: string;
  username: string;
  full_name: string;
  role: string;
  is_active: boolean;
  last_login?: string;
  login_count: number;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  admin: AdminUser;
}

export interface AuthContextType {
  user: AdminUser | null;
  isAuthenticated: boolean;
  token: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
  error: string | null;
}
