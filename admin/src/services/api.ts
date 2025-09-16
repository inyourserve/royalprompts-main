/**
 * API Service for RoyalPrompts Admin Panel
 * Handles all backend communication with proper authentication
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiResponse<T = any> {
  success?: boolean;
  data?: T;
  error?: string;
  detail?: string;
  message?: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  admin: {
    id: string;
    email: string;
    username: string;
    full_name: string;
    role: string;
    is_active: boolean;
  };
}

class ApiService {
  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('royalprompts_token');
    }
    return null;
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    const token = this.getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get('content-type');
    
    if (!contentType || !contentType.includes('application/json')) {
      throw new Error(`Server error: ${response.status}`);
    }

    const data = await response.json();

    if (!response.ok) {
      const errorMessage = data.detail || data.error || data.message || `HTTP ${response.status}`;
      throw new Error(errorMessage);
    }

    return data;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const config: RequestInit = {
      headers: this.getHeaders(),
      ...options,
    };

    try {
      const response = await fetch(url, config);
      return this.handleResponse<T>(response);
    } catch (error) {
      console.error(`API Error for ${endpoint}:`, error);
      throw error;
    }
  }

  // Authentication Methods
  async login(email: string, password: string): Promise<LoginResponse> {
    return this.request<LoginResponse>('/api/admin/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async getCurrentAdmin(): Promise<any> {
    return this.request('/api/admin/auth/me');
  }

  // Dashboard Methods
  async getDashboardStats(): Promise<any> {
    return this.request('/api/admin/dashboard');
  }

  async getRecentPrompts(): Promise<any> {
    // Get recent prompts for dashboard
    const response = await this.getPrompts({ page: 1, limit: 5 });
    return { prompts: response.items || [] };
  }

  async getChartData(): Promise<any> {
    // Mock chart data in the format expected by PromptsChart component
    return {
      prompts_added: [45, 52, 38, 67, 58, 72, 89, 76, 85, 92, 78, 95],
      trending_prompts: [12, 18, 15, 25, 22, 28, 35, 30, 32, 38, 29, 42],
      totals: { 
        total_prompts_added: 892, 
        total_trending: 327 
      }
    };
  }

  // Prompts Methods
  async getPrompts(params: {
    page?: number;
    limit?: number;
    status?: string;
    category_id?: string;
    is_featured?: boolean;
    search?: string;
  } = {}): Promise<PaginatedResponse<any>> {
    const searchParams = new URLSearchParams();
    
    if (params.page) searchParams.append('page', params.page.toString());
    if (params.limit) searchParams.append('limit', params.limit.toString());
    if (params.status) searchParams.append('status', params.status);
    if (params.category_id) searchParams.append('category_id', params.category_id);
    if (params.search) searchParams.append('search', params.search);

    const queryString = searchParams.toString();
    const endpoint = `/api/admin/prompts${queryString ? `?${queryString}` : ''}`;
    
    return this.request<PaginatedResponse<any>>(endpoint);
  }

  async searchPrompts(query: string, page = 1, limit = 20): Promise<PaginatedResponse<any>> {
    const searchParams = new URLSearchParams({
      search: query,
      page: page.toString(),
      limit: limit.toString(),
    });
    
    return this.request<PaginatedResponse<any>>(`/api/admin/prompts?${searchParams}`);
  }

  async createPrompt(promptData: any): Promise<any> {
    return this.request('/api/admin/prompts', {
      method: 'POST',
      body: JSON.stringify(promptData),
    });
  }

  async updatePrompt(id: string, promptData: any): Promise<any> {
    return this.request(`/api/admin/prompts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(promptData),
    });
  }

  async deletePrompt(id: string): Promise<any> {
    return this.request(`/api/admin/prompts/${id}`, {
      method: 'DELETE',
    });
  }

  // Feature/status changes will be handled via updatePrompt with status field
  async featurePrompt(id: string): Promise<any> {
    return this.updatePrompt(id, { is_featured: true });
  }

  async unfeaturePrompt(id: string): Promise<any> {
    return this.updatePrompt(id, { is_featured: false });
  }

  async publishPrompt(id: string): Promise<any> {
    return this.updatePrompt(id, { status: 'published' });
  }

  async archivePrompt(id: string): Promise<any> {
    return this.updatePrompt(id, { status: 'archived' });
  }

  // Note: Categories and Users management have been simplified in this version
  // These features can be re-enabled by creating separate backend endpoints if needed

  // Category Methods
  async getCategories(params: {
    page?: number;
    limit?: number;
    search?: string;
    is_active?: boolean;
  } = {}): Promise<PaginatedResponse<any>> {
    const searchParams = new URLSearchParams();
    
    if (params.page) searchParams.append('page', params.page.toString());
    if (params.limit) searchParams.append('limit', params.limit.toString());
    if (params.search) searchParams.append('search', params.search);
    if (params.is_active !== undefined) searchParams.append('is_active', params.is_active.toString());

    const queryString = searchParams.toString();
    const endpoint = `/api/admin/categories${queryString ? `?${queryString}` : ''}`;
    
    return this.request<PaginatedResponse<any>>(endpoint);
  }

  async createCategory(categoryData: any): Promise<any> {
    return this.request('/api/admin/categories', {
      method: 'POST',
      body: JSON.stringify(categoryData),
    });
  }

  async updateCategory(id: string, categoryData: any): Promise<any> {
    return this.request(`/api/admin/categories/${id}`, {
      method: 'PUT',
      body: JSON.stringify(categoryData),
    });
  }

  async deleteCategory(id: string): Promise<any> {
    return this.request(`/api/admin/categories/${id}`, {
      method: 'DELETE',
    });
  }

  async toggleCategoryStatus(id: string): Promise<any> {
    return this.request(`/api/admin/categories/${id}/toggle-status`, {
      method: 'POST',
    });
  }

  // File Upload Method (Admin only for prompt images)
  async uploadFile(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const token = this.getAuthToken();
    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/api/admin/prompts/upload-image`, {
      method: 'POST',
      headers,
      body: formData,
    });

    return this.handleResponse(response);
  }
}

export const apiService = new ApiService();
export default apiService;
