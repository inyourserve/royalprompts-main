/**
 * Category API service
 */

import { BaseApiService } from './base-api';
import { 
  // Category, 
  CategoryCreate, 
  CategoryUpdate, 
  CategoryAdmin, 
  CategoryFilters,
  PaginatedResponse 
} from '@/types';

export class CategoryApiService extends BaseApiService {
  async getCategories(filters: CategoryFilters = {}): Promise<PaginatedResponse<CategoryAdmin>> {
    const searchParams = new URLSearchParams();
    
    if (filters.page) searchParams.append('page', filters.page.toString());
    if (filters.limit) searchParams.append('limit', filters.limit.toString());
    if (filters.search) searchParams.append('search', filters.search);
    if (filters.is_active !== undefined) searchParams.append('is_active', filters.is_active.toString());

    const queryString = searchParams.toString();
    const endpoint = `/api/admin/categories${queryString ? `?${queryString}` : ''}`;
    
    return this.request<PaginatedResponse<CategoryAdmin>>(endpoint);
  }

  async getCategoryById(id: string): Promise<CategoryAdmin> {
    return this.request<CategoryAdmin>(`/api/admin/categories/${id}`);
  }


  async createCategory(categoryData: CategoryCreate): Promise<CategoryAdmin> {
    return this.request<CategoryAdmin>('/api/admin/categories', {
      method: 'POST',
      body: JSON.stringify(categoryData),
    });
  }

  async updateCategory(id: string, categoryData: CategoryUpdate): Promise<CategoryAdmin> {
    return this.request<CategoryAdmin>(`/api/admin/categories/${id}`, {
      method: 'PUT',
      body: JSON.stringify(categoryData),
    });
  }

  async deleteCategory(id: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/admin/categories/${id}`, {
      method: 'DELETE',
    });
  }

  async toggleStatus(id: string): Promise<CategoryAdmin> {
    return this.request<CategoryAdmin>(`/api/admin/categories/${id}/toggle-status`, {
      method: 'POST',
    });
  }

  async searchCategories(query: string, page = 1, limit = 20): Promise<PaginatedResponse<CategoryAdmin>> {
    const searchParams = new URLSearchParams({
      search: query,
      page: page.toString(),
      limit: limit.toString(),
    });
    
    return this.request<PaginatedResponse<CategoryAdmin>>(`/api/admin/categories?${searchParams}`);
  }
}

export const categoryApi = new CategoryApiService();
