/**
 * Prompt API service
 */

import { BaseApiService } from './base-api';
import { 
  // Prompt, 
  PromptCreate, 
  PromptUpdate, 
  PromptAdmin, 
  PromptFilters,
  PaginatedResponse,
  ImageUploadResponse 
} from '@/types';

export class PromptApiService extends BaseApiService {
  async getPrompts(filters: PromptFilters = {}): Promise<PaginatedResponse<PromptAdmin>> {
    const searchParams = new URLSearchParams();
    
    if (filters.page) searchParams.append('page', filters.page.toString());
    if (filters.limit) searchParams.append('limit', filters.limit.toString());
    if (filters.status) searchParams.append('status', filters.status);
    if (filters.category_id) searchParams.append('category_id', filters.category_id);
    if (filters.search) searchParams.append('search', filters.search);
    if (filters.is_featured !== undefined) searchParams.append('is_featured', filters.is_featured.toString());

    const queryString = searchParams.toString();
    const endpoint = `/api/admin/prompts${queryString ? `?${queryString}` : ''}`;
    
    return this.request<PaginatedResponse<PromptAdmin>>(endpoint);
  }

  async getPromptById(id: string): Promise<PromptAdmin> {
    return this.request<PromptAdmin>(`/api/admin/prompts/${id}`);
  }


  async createPrompt(promptData: PromptCreate): Promise<PromptAdmin> {
    return this.request<PromptAdmin>('/api/admin/prompts', {
      method: 'POST',
      body: JSON.stringify(promptData),
    });
  }

  async updatePrompt(id: string, promptData: PromptUpdate): Promise<PromptAdmin> {
    return this.request<PromptAdmin>(`/api/admin/prompts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(promptData),
    });
  }

  async deletePrompt(id: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/admin/prompts/${id}`, {
      method: 'DELETE',
    });
  }

  async uploadImage(file: File): Promise<ImageUploadResponse> {
    return this.uploadFile('/api/admin/prompts/upload-image', file);
  }

  async uploadTempImage(file: File): Promise<ImageUploadResponse> {
    return this.uploadFile('/api/admin/prompts/upload-temp-image', file);
  }

  async searchPrompts(query: string, page = 1, limit = 20): Promise<PaginatedResponse<PromptAdmin>> {
    const searchParams = new URLSearchParams({
      search: query,
      page: page.toString(),
      limit: limit.toString(),
    });
    
    return this.request<PaginatedResponse<PromptAdmin>>(`/api/admin/prompts?${searchParams}`);
  }

  // Feature/status operations
  async featurePrompt(id: string): Promise<PromptAdmin> {
    return this.updatePrompt(id, { is_featured: true });
  }

  async unfeaturePrompt(id: string): Promise<PromptAdmin> {
    return this.updatePrompt(id, { is_featured: false });
  }

  async publishPrompt(id: string): Promise<PromptAdmin> {
    return this.updatePrompt(id, { status: 'published' });
  }

  async archivePrompt(id: string): Promise<PromptAdmin> {
    return this.updatePrompt(id, { status: 'draft' });
  }
}

export const promptApi = new PromptApiService();
