/**
 * Export all API services from a central location
 */

// API Services
export { authApi } from './auth-api';
export { promptApi } from './prompt-api';
export { categoryApi } from './category-api';
export { dashboardApi } from './dashboard-api';
export { settingsApi } from './settings-api';
export { socialLinksApi } from './social-links-api';
export { usersApi } from './users-api';

// Types
export * from '@/types';

// Legacy support (for gradual migration)
export { apiService } from './api';
