"use client";
import React, { useState, useEffect } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableRow,
} from "../ui/table";
import Badge from "../ui/badge/Badge";
import Image from "next/image";
import ComponentCard from "../common/ComponentCard";
import { getImageDimensions, getFullImageUrl } from "@/utils/image";
import { dashboardApi, categoryApi } from "@/services";
import ImagePreviewModal from "../common/ImagePreviewModal";

interface Prompt {
  id: string;
  title: string;
  description?: string;
  content?: string;
  category_id?: string;
  category_name?: string;
  status?: string;
  is_featured?: boolean;
  is_active?: boolean;
  image_url?: string;
  created_at: string;
  // Legacy/fallback fields for mock data
  category?: string;
  prompt_text?: string;
  tags?: string[];
  is_trending?: boolean;
  image?: string;
}

export default function RecentPrompts() {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [previewModal, setPreviewModal] = useState<{
    isOpen: boolean;
    imageUrl?: string;
    title?: string;
  }>({ isOpen: false });

  const getCategoryName = (categoryId: string) => {
    const category = categories.find(cat => cat.id === categoryId);
    return category?.name || "Uncategorized";
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch both prompts and categories in parallel
        const [promptsResponse, categoriesResponse] = await Promise.all([
          dashboardApi.getRecentPrompts(),
          categoryApi.getCategories()
        ]);
        
        setPrompts(promptsResponse.prompts || []);
        setCategories(categoriesResponse.items || []);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
        setError(err instanceof Error ? err.message : "Failed to load dashboard data");
        
        // Fallback to mock data if API fails
        setPrompts([
          {
            id: "1",
            title: "Professional Email Writer",
            category: "Business",
            prompt_text: "Write a professional email for...",
            tags: ["email", "professional", "business"],
            is_trending: true,
            created_at: "2024-01-15",
            image: "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop",
          },
          {
            id: "2",
            title: "Creative Story Generator",
            category: "Creative Writing",
            prompt_text: "Create a creative story about...",
            tags: ["story", "creative", "fiction"],
            is_trending: false,
            created_at: "2024-01-14",
            image: "https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=400&h=400&fit=crop",
          },
        ]);
        setCategories([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <ComponentCard
        title="Recently Added Prompts"
        desc="Latest prompts added to the platform"
      >
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, index) => (
            <div key={index} className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gray-200 rounded-lg dark:bg-gray-700"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4 dark:bg-gray-700"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2 dark:bg-gray-700"></div>
              </div>
            </div>
          ))}
        </div>
      </ComponentCard>
    );
  }

  if (error && prompts.length === 0) {
    return (
      <ComponentCard
        title="Recently Added Prompts"
        desc="Latest prompts added to the platform"
      >
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20">
          <p className="text-red-600 dark:text-red-400">Failed to load recent prompts: {error}</p>
        </div>
      </ComponentCard>
    );
  }

  return (
    <ComponentCard
      title="Recently Added Prompts"
      desc="Latest prompts added to the platform"
    >
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
        <div className="max-w-full overflow-x-auto">
          <div className="min-w-[800px]">
            <Table>
              <TableHeader className="border-b border-gray-100 dark:border-gray-800">
                <TableRow className="bg-gray-50 dark:bg-gray-800">
                  <TableCell
                    isHeader
                    className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400"
                  >
                    Prompt
                  </TableCell>
                  <TableCell
                    isHeader
                    className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400"
                  >
                    Category
                  </TableCell>
                  <TableCell
                    isHeader
                    className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400"
                  >
                    Status
                  </TableCell>
                  <TableCell
                    isHeader
                    className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400"
                  >
                    Added
                  </TableCell>
                </TableRow>
              </TableHeader>
              <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
                {prompts.map((prompt) => (
                  <TableRow key={prompt.id} className="bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800">
                    <TableCell className="px-5 py-4 sm:px-6 text-start">
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-12 h-12 overflow-hidden rounded-lg cursor-pointer hover:opacity-80 transition-opacity"
                          onClick={() => setPreviewModal({
                            isOpen: true,
                            imageUrl: prompt.image_url || prompt.image,
                            title: prompt.title
                          })}
                        >
                          <Image
                            {...getImageDimensions('prompt')}
                            src={getFullImageUrl(prompt.image_url || prompt.image)}
                            alt={prompt.title}
                            className="w-full h-full object-cover"
                          />
                        </div>
                        <div>
                          <span className="block font-medium text-gray-800 text-theme-sm dark:text-white">
                            {prompt.title}
                          </span>
                          <span className="block text-gray-500 text-theme-xs dark:text-gray-400">
                            {prompt.description || prompt.content?.substring(0, 60) + '...' || prompt.prompt_text?.substring(0, 60) + '...' || 'No description'}
                          </span>
                          <div className="flex gap-1 mt-1">
                            {prompt.tags && prompt.tags.length > 0 ? prompt.tags.slice(0, 2).map((tag, index) => (
                              <Badge key={index} color="light" size="sm">
                                {tag}
                              </Badge>
                            )) : (
                              <Badge color="light" size="sm">
                                {prompt.status || "draft"}
                              </Badge>
                            )}
                            {prompt.tags && prompt.tags.length > 2 && (
                              <Badge color="light" size="sm">
                                +{prompt.tags.length - 2}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="px-4 py-3 text-start">
                      <Badge color="primary" size="sm">
                        {prompt.category_id ? getCategoryName(prompt.category_id) : (prompt.category_name || prompt.category || "Uncategorized")}
                      </Badge>
                    </TableCell>
                    <TableCell className="px-4 py-3 text-start">
                      <Badge
                        color={prompt.is_featured || prompt.is_trending ? "success" : (prompt.is_active !== false ? "primary" : "warning")}
                        size="sm"
                      >
                        {prompt.is_featured || prompt.is_trending ? "Featured" : (prompt.is_active !== false ? "Active" : "Inactive")}
                      </Badge>
                    </TableCell>
                    <TableCell className="px-4 py-3 text-gray-500 text-theme-sm dark:text-gray-400">
                      {new Date(prompt.created_at).toLocaleDateString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
    </ComponentCard>

    {/* Image Preview Modal */}
    <ImagePreviewModal
      isOpen={previewModal.isOpen}
      onClose={() => setPreviewModal({ isOpen: false })}
      imageUrl={previewModal.imageUrl}
      title={previewModal.title}
      alt="Prompt Image"
    />
  );
}
