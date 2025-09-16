/**
 * Settings related types
 */

export interface AppSettings {
  id?: string;
  app_name: string;
  description: string;
  about_text?: string;
  how_to_use?: string;
  contact_email: string;
  created_at?: string;
  updated_at?: string;
}

export interface AppSettingsUpdate {
  app_name?: string;
  description?: string;
  about_text?: string;
  how_to_use?: string;
  contact_email?: string;
}

export interface AppSettingsCreate {
  app_name: string;
  description: string;
  about_text?: string;
  how_to_use?: string;
  contact_email: string;
}
