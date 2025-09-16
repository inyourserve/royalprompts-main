/**
 * Social Links API service
 */

import { BaseApiService } from './base-api';

export interface SocialLink {
  id?: string;
  platform: string;
  url: string;
  is_active: boolean;
  display_order: number;
  created_at?: string;
  updated_at?: string;
}

export interface SocialLinkUpdate {
  platform?: string;
  url?: string;
  is_active?: boolean;
  display_order?: number;
}

export interface SocialLinksListResponse {
  items: SocialLink[];
  total: number;
}

export class SocialLinksApiService extends BaseApiService {
  async getSocialLinks(): Promise<SocialLinksListResponse> {
    return this.request<SocialLinksListResponse>('/api/admin/social-links/');
  }

  async getActiveSocialLinks(): Promise<SocialLinksListResponse> {
    return this.request<SocialLinksListResponse>('/api/admin/social-links/active');
  }

  async createSocialLink(link: Omit<SocialLink, 'id' | 'created_at' | 'updated_at'>): Promise<SocialLink> {
    return this.request<SocialLink>('/api/admin/social-links/', {
      method: 'POST',
      body: JSON.stringify(link),
    });
  }

  async updateSocialLink(id: string, link: SocialLinkUpdate): Promise<SocialLink> {
    return this.request<SocialLink>(`/api/admin/social-links/${id}`, {
      method: 'PUT',
      body: JSON.stringify(link),
    });
  }

  async bulkUpdateSocialLinks(links: SocialLinkUpdate[]): Promise<SocialLinksListResponse> {
    return this.request<SocialLinksListResponse>('/api/admin/social-links/bulk', {
      method: 'PUT',
      body: JSON.stringify({ links }),
    });
  }

  async deleteSocialLink(id: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/admin/social-links/${id}`, {
      method: 'DELETE',
    });
  }

  async resetSocialLinks(): Promise<SocialLinksListResponse> {
    return this.request<SocialLinksListResponse>('/api/admin/social-links/reset', {
      method: 'POST',
    });
  }
}

export const socialLinksApi = new SocialLinksApiService();
