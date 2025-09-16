/**
 * Prompt related types
 */

import { BaseEntity, PaginationParams, SearchParams, SortParams } from './common';

export type PromptStatus = 'draft' | 'published';

export interface BasePrompt {
  title: string;
  description: string;
  content: string;
  category_id: string;
}

export interface Prompt extends BaseEntity, BasePrompt {
  image_url?: string;
  status: PromptStatus;
  is_featured: boolean;
  is_active: boolean;
  likes_count: number;
  created_by?: string;
}

export interface PromptCreate extends BasePrompt {
  image_url?: string;
  is_featured?: boolean;
  status?: PromptStatus;
}

export interface PromptUpdate {
  title?: string;
  description?: string;
  content?: string;
  image_url?: string;
  category_id?: string;
  status?: PromptStatus;
  is_featured?: boolean;
  is_active?: boolean;
}

export interface PromptSummary {
  id: string;
  title: string;
  description: string;
  image_url?: string;
  category_id: string;
  is_featured: boolean;
  likes_count: number;
  created_at: string;
}

export interface PromptDetail extends Prompt {
  category_name?: string;
}

export interface PromptAdmin extends Prompt {
  // Inherits all fields from Prompt - no additional fields needed
}

export interface PromptFilters extends PaginationParams, SearchParams, SortParams {
  status?: PromptStatus;
  category_id?: string;
  is_featured?: boolean;
}

export interface PromptStats {
  total_prompts: number;
  published_prompts: number;
  draft_prompts: number;
  featured_prompts: number;
  total_likes: number;
}

export interface PromptChartData {
  prompts_added: number[];
  trending_prompts: number[];
  totals: {
    total_prompts_added: number;
    total_trending: number;
  };
}
