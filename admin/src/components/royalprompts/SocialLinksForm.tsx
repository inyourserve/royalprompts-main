"use client";
import React, { useState, useEffect } from "react";
import ComponentCard from "../common/ComponentCard";
import Button from "../ui/button/Button";
import Input from "../form/input/InputField";
import Label from "../form/Label";
import { CheckCircleIcon } from "@/icons";
import Alert from "../ui/alert/Alert";
import { socialLinksApi, SocialLink } from "@/services";

interface SocialLinkFormData {
  platform: string;
  url: string;
  isActive: boolean;
}

export default function SocialLinksForm() {
  const [socialLinks, setSocialLinks] = useState<SocialLink[]>([]);
  const [isSaved, setIsSaved] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load social links on component mount
  useEffect(() => {
    const fetchSocialLinks = async () => {
      try {
        setIsLoadingData(true);
        const response = await socialLinksApi.getSocialLinks();
        setSocialLinks(response.items);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch social links:", err);
        setError(err instanceof Error ? err.message : "Failed to load social links");
        
        // Set default values if API fails
        setSocialLinks([
          { platform: "Twitter", url: "https://twitter.com/royalprompts", is_active: true, display_order: 1 },
          { platform: "Facebook", url: "https://facebook.com/royalprompts", is_active: true, display_order: 2 },
          { platform: "Instagram", url: "https://instagram.com/royalprompts", is_active: true, display_order: 3 },
          { platform: "LinkedIn", url: "https://linkedin.com/company/royalprompts", is_active: false, display_order: 4 },
          { platform: "YouTube", url: "https://youtube.com/@royalprompts", is_active: false, display_order: 5 },
          { platform: "Discord", url: "https://discord.gg/royalprompts", is_active: true, display_order: 6 },
        ]);
      } finally {
        setIsLoadingData(false);
      }
    };

    fetchSocialLinks();
  }, []);

  const handleUrlChange = (index: number, url: string) => {
    const updatedLinks = [...socialLinks];
    updatedLinks[index].url = url;
    setSocialLinks(updatedLinks);
  };

  const handleToggleActive = (index: number) => {
    const updatedLinks = [...socialLinks];
    updatedLinks[index].is_active = !updatedLinks[index].is_active;
    setSocialLinks(updatedLinks);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    try {
      // Prepare update data
      const updateData = socialLinks.map(link => ({
        platform: link.platform,
        url: link.url,
        is_active: link.is_active,
        display_order: link.display_order
      }));

      await socialLinksApi.bulkUpdateSocialLinks(updateData);
      
      setIsSaved(true);
      
      // Hide success message after 3 seconds
      setTimeout(() => setIsSaved(false), 3000);
    } catch (err) {
      console.error("Failed to save social links:", err);
      setError(err instanceof Error ? err.message : "Failed to save social links");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await socialLinksApi.resetSocialLinks();
      setSocialLinks(response.items);
      
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 3000);
    } catch (err) {
      console.error("Failed to reset social links:", err);
      setError(err instanceof Error ? err.message : "Failed to reset social links");
    } finally {
      setIsLoading(false);
    }
  };

  const getPlatformIcon = (platform: string) => {
    switch (platform.toLowerCase()) {
      case "twitter":
        return "🐦";
      case "facebook":
        return "📘";
      case "instagram":
        return "📷";
      case "linkedin":
        return "💼";
      case "youtube":
        return "📺";
      case "discord":
        return "🎮";
      default:
        return "🔗";
    }
  };

  const getPlatformColor = (platform: string) => {
    switch (platform.toLowerCase()) {
      case "twitter":
        return "text-blue-500";
      case "facebook":
        return "text-blue-600";
      case "instagram":
        return "text-pink-500";
      case "linkedin":
        return "text-blue-700";
      case "youtube":
        return "text-red-500";
      case "discord":
        return "text-indigo-500";
      default:
        return "text-gray-500";
    }
  };

  if (isLoadingData) {
    return (
      <ComponentCard
        title="Social Media Links"
        desc="Manage your social media presence and links"
      >
        <div className="animate-pulse space-y-6">
          {[...Array(6)].map((_, index) => (
            <div key={index} className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="h-6 w-6 bg-gray-200 rounded dark:bg-gray-700"></div>
                  <div className="h-4 bg-gray-200 rounded w-20 dark:bg-gray-700"></div>
                </div>
                <div className="h-4 bg-gray-200 rounded w-16 dark:bg-gray-700"></div>
              </div>
              <div className="h-10 bg-gray-200 rounded dark:bg-gray-700"></div>
            </div>
          ))}
        </div>
      </ComponentCard>
    );
  }

  return (
    <ComponentCard
      title="Social Media Links"
      desc="Manage your social media presence and links"
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
          title="Links Updated"
          message="Your social media links have been successfully updated."
        />
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {socialLinks.map((link, index) => (
            <div key={link.platform} className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{getPlatformIcon(link.platform)}</span>
                  <Label className={`font-medium ${getPlatformColor(link.platform)}`}>
                    {link.platform}
                  </Label>
                </div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={link.is_active}
                    onChange={() => handleToggleActive(index)}
                    className="w-4 h-4 text-brand-500 bg-gray-100 border-gray-300 rounded focus:ring-brand-500 dark:focus:ring-brand-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                  />
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Active
                  </span>
                </label>
              </div>
              
              <Input
                type="url"
                value={link.url}
                onChange={(e) => handleUrlChange(index, e.target.value)}
                placeholder={`Enter ${link.platform} URL`}
                disabled={!link.is_active}
                className={!link.is_active ? "opacity-50" : ""}
              />
              
              {link.is_active && link.url && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-gray-500 dark:text-gray-400">Preview:</span>
                  <a
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-brand-500 hover:text-brand-600 dark:hover:text-brand-400 truncate"
                  >
                    {link.url}
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Instructions */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
            Instructions
          </h4>
          <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
            <li>• Toggle the &quot;Active&quot; checkbox to enable/disable each social link</li>
            <li>• Enter the full URL including https:// for each platform</li>
            <li>• Links will be displayed on your public profile and footer</li>
            <li>• Only active links will be shown to users</li>
          </ul>
        </div>

        {/* Preview */}
        <div className="border-t border-gray-200 dark:border-gray-800 pt-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Preview
          </h3>
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <div className="flex flex-wrap gap-3">
              {socialLinks
                .filter(link => link.is_active && link.url)
                .map(link => (
                  <a
                    key={link.platform}
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 hover:border-brand-300 dark:hover:border-brand-500 transition-colors"
                  >
                    <span className="text-lg">{getPlatformIcon(link.platform)}</span>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {link.platform}
                    </span>
                  </a>
                ))}
            </div>
            {socialLinks.filter(link => link.is_active && link.url).length === 0 && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                No active social links to display
              </p>
            )}
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
            {isLoading ? "Saving..." : "Save Social Links"}
          </Button>
        </div>
      </form>
    </ComponentCard>
  );
}
