"use client";
import React, { useState, useEffect } from "react";
import ComponentCard from "../common/ComponentCard";
import Button from "../ui/button/Button";
import Input from "../form/input/InputField";
import Label from "../form/Label";
import TextArea from "../form/input/TextArea";
import { CheckCircleIcon } from "@/icons";
import Alert from "../ui/alert/Alert";
import { settingsApi } from "@/services";
import { AppSettings } from "@/types";

interface AppSettingsFormData {
  appName: string;
  description: string;
  aboutText: string;
  howToUse: string;
  contactEmail: string;
}

export default function AppSettingsForm() {
  const [settings, setSettings] = useState<AppSettingsFormData>({
    appName: "",
    description: "",
    aboutText: "",
    howToUse: "",
    contactEmail: "",
  });

  const [isSaved, setIsSaved] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load settings on component mount
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setIsLoadingData(true);
        const response = await settingsApi.getAppSettings();
        setSettings({
          appName: response.app_name,
          description: response.description,
          aboutText: response.about_text || "",
          howToUse: response.how_to_use || "",
          contactEmail: response.contact_email,
        });
        setError(null);
      } catch (err) {
        console.error("Failed to fetch settings:", err);
        setError(err instanceof Error ? err.message : "Failed to load settings");
        
        // Set default values if API fails
        setSettings({
          appName: "RoyalPrompts",
          description: "Your AI prompt management platform",
          aboutText: "RoyalPrompts is a comprehensive platform for managing and organizing AI prompts. We help users discover, create, and share high-quality prompts for various AI models.",
          howToUse: "1. Browse prompts by category\n2. Copy and use prompts with your AI\n3. Create and share your own prompts\n4. Save favorites for quick access",
          contactEmail: "support@royalprompts.com",
        });
      } finally {
        setIsLoadingData(false);
      }
    };

    fetchSettings();
  }, []);

  const handleInputChange = (field: keyof AppSettingsFormData, value: string) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    try {
      await settingsApi.updateAppSettings({
        app_name: settings.appName,
        description: settings.description,
        about_text: settings.aboutText,
        how_to_use: settings.howToUse,
        contact_email: settings.contactEmail,
      });
      
      setIsSaved(true);
      
      // Hide success message after 3 seconds
      setTimeout(() => setIsSaved(false), 3000);
    } catch (err) {
      console.error("Failed to save settings:", err);
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await settingsApi.resetAppSettings();
      setSettings({
        appName: response.app_name,
        description: response.description,
        aboutText: response.about_text || "",
        howToUse: response.how_to_use || "",
        contactEmail: response.contact_email,
      });
      
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 3000);
    } catch (err) {
      console.error("Failed to reset settings:", err);
      setError(err instanceof Error ? err.message : "Failed to reset settings");
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoadingData) {
    return (
      <ComponentCard
        title="App Settings"
        desc="Configure general application settings"
      >
        <div className="animate-pulse space-y-6">
          {[...Array(5)].map((_, index) => (
            <div key={index} className="space-y-2">
              <div className="h-4 bg-gray-200 rounded w-24 dark:bg-gray-700"></div>
              <div className="h-10 bg-gray-200 rounded dark:bg-gray-700"></div>
            </div>
          ))}
        </div>
      </ComponentCard>
    );
  }

  return (
    <ComponentCard
      title="App Settings"
      desc="Configure general application settings"
    >
      {error && (
        <Alert
          variant="error"
          title="Error"
          message={error}
        />
      )}
      
      {isSaved && (
        <Alert
          variant="success"
          title="Settings Saved"
          message="Your app settings have been successfully updated."
        />
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* App Name */}
        <div>
          <Label>App Name <span className="text-error-500">*</span></Label>
          <Input
            type="text"
            value={settings.appName}
            onChange={(e) => handleInputChange('appName', e.target.value)}
            placeholder="Enter app name"
          />
        </div>

        {/* Description */}
        <div>
          <Label>App Description <span className="text-error-500">*</span></Label>
          <Input
            type="text"
            value={settings.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            placeholder="Enter app description"
          />
        </div>

        {/* About Text */}
        <div>
          <Label>About Text</Label>
          <TextArea
            value={settings.aboutText}
            onChange={(value) => handleInputChange('aboutText', value)}
            placeholder="Enter about text"
            rows={4}
          />
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            This text will be displayed on the about page
          </p>
        </div>

        {/* How to Use */}
        <div>
          <Label>How to Use</Label>
          <TextArea
            value={settings.howToUse}
            onChange={(value) => handleInputChange('howToUse', value)}
            placeholder="Enter instructions on how to use the app"
            rows={6}
          />
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Provide step-by-step instructions for users
          </p>
        </div>

        {/* Contact Email */}
        <div>
          <Label>Contact Email <span className="text-error-500">*</span></Label>
          <Input
            type="email"
            value={settings.contactEmail}
            onChange={(e) => handleInputChange('contactEmail', e.target.value)}
            placeholder="Enter contact email"
          />
        </div>

        {/* Preview Section */}
        <div className="border-t border-gray-200 dark:border-gray-800 pt-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Preview
          </h3>
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-3">
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white">
                {settings.appName}
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {settings.description}
              </p>
            </div>
            <div>
              <h5 className="font-medium text-gray-900 dark:text-white text-sm">
                About
              </h5>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {settings.aboutText}
              </p>
            </div>
            <div>
              <h5 className="font-medium text-gray-900 dark:text-white text-sm">
                How to Use
              </h5>
              <pre className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
                {settings.howToUse}
              </pre>
            </div>
            <div>
              <h5 className="font-medium text-gray-900 dark:text-white text-sm">
                Contact
              </h5>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {settings.contactEmail}
              </p>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex items-center justify-end gap-3 pt-6 border-t border-gray-200 dark:border-gray-800">
          <Button
            type="button"
            variant="outline"
            onClick={handleReset}
            disabled={isLoading}
          >
            {isLoading ? "Resetting..." : "Reset to Default"}
          </Button>
          <Button
            type="submit"
            disabled={isLoading}
            startIcon={isLoading ? undefined : <CheckCircleIcon />}
          >
            {isLoading ? "Saving..." : "Save Settings"}
          </Button>
        </div>
      </form>
    </ComponentCard>
  );
}
