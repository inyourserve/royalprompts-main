/**
 * Common types used across the application
 */

export interface ApiResponse<T = any> {
  success?: boolean;
  data?: T;
  error?: string;
  detail?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit?: number;
  size?: number;
  pages?: number;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  skip?: number;
}

export interface BaseEntity {
  id: string;
  created_at: string;
  updated_at?: string;
}

export interface ImageUploadResponse {
  filename: string;
  url: string;
  thumbnail_url?: string;
  size: number;
  content_type: string;
  width?: number;
  height?: number;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  database: string;
}

export type SortOrder = 'asc' | 'desc';

export interface SortParams {
  field?: string;
  order?: SortOrder;
}

export interface SearchParams {
  search?: string;
  query?: string;
}
