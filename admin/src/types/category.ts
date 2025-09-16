/**
 * Category related types
 */

import { BaseEntity, PaginationParams, SearchParams, SortParams } from './common';

export interface BaseCategory {
  name: string;
  description?: string;
  icon?: string;
}

export interface Category extends BaseEntity, BaseCategory {
  order: number;
  is_active: boolean;
  prompts_count: number;
}

export interface CategoryCreate extends BaseCategory {
  order?: number;
}

export interface CategoryUpdate {
  name?: string;
  description?: string;
  icon?: string;
  order?: number;
  is_active?: boolean;
}

export interface CategorySummary {
  id: string;
  name: string;
  icon?: string;
  prompts_count: number;
}

export interface CategoryAdmin extends Category {
  created_by?: string;
}

export interface CategoryFilters extends PaginationParams, SearchParams, SortParams {
  is_active?: boolean;
}

export interface CategoryStats {
  total_categories: number;
  active_categories: number;
}
