"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableRow,
} from "../ui/table";
import Badge from "../ui/badge/Badge";
import Button from "../ui/button/Button";
import Image from "next/image";
import { PencilIcon, TrashBinIcon, PlusIcon, SearchIcon } from "@/icons";
import { Dropdown } from "../ui/dropdown/Dropdown";
import { DropdownItem } from "../ui/dropdown/DropdownItem";
import ComponentCard from "../common/ComponentCard";
import { getImageDimensions, getFullImageUrl } from "@/utils/image";
import { promptApi, categoryApi, PromptAdmin, CategoryAdmin } from "@/services";
import ImagePreviewModal from "../common/ImagePreviewModal";

export default function PromptsTable() {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [isCategoryDropdownOpen, setIsCategoryDropdownOpen] = useState(false);
  const [prompts, setPrompts] = useState<PromptAdmin[]>([]);
  const [categories, setCategories] = useState<CategoryAdmin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPrompts, setTotalPrompts] = useState(0);
  const [previewModal, setPreviewModal] = useState<{
    isOpen: boolean;
    imageUrl?: string;
    title?: string;
  }>({ isOpen: false });
  const pageSize = 10;

  // Helper function to get category name from category ID
  const getCategoryName = (categoryId: string): string => {
    const category = categories.find(cat => cat.id === categoryId);
    return category ? category.name : categoryId;
  };

  // Fetch prompts and categories
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch prompts
        const promptsResponse = await promptApi.getPrompts({
          page: currentPage,
          limit: pageSize,
          search: searchTerm || undefined,
          category_id: selectedCategory !== "All" ? selectedCategory : undefined,
        });
        
        setPrompts(promptsResponse.items || []);
        setTotalPrompts(promptsResponse.total || 0);
        
        // Fetch categories from API
        if (categories.length === 0) {
          try {
            const categoriesResponse = await categoryApi.getCategories({ limit: 50 });
            setCategories(categoriesResponse.items || []);
          } catch (catError) {
            console.error("Failed to fetch categories:", catError);
            // Fallback to static categories
            setCategories([
              { id: "new", name: "New", order: 1, is_active: true, prompts_count: 0, created_at: "2024-01-15T00:00:00Z", updated_at: "2024-01-15T00:00:00Z" },
              { id: "trending", name: "Trending", order: 2, is_active: true, prompts_count: 0, created_at: "2024-01-15T00:00:00Z", updated_at: "2024-01-15T00:00:00Z" },
              { id: "cinematic", name: "Cinematic", order: 3, is_active: true, prompts_count: 0, created_at: "2024-01-15T00:00:00Z", updated_at: "2024-01-15T00:00:00Z" },
              { id: "portra", name: "Portra", order: 4, is_active: true, prompts_count: 0, created_at: "2024-01-15T00:00:00Z", updated_at: "2024-01-15T00:00:00Z" },
            ]);
          }
        }
        
        setError(null);
      } catch (err) {
        console.error("Failed to fetch prompts:", err);
        setError(err instanceof Error ? err.message : "Failed to load prompts");
        
        // Fallback to mock data with simplified structure
        const mockPrompt: PromptAdmin = {
          id: "1",
          title: "Professional Email Writer",
          description: "Professional email writing assistant",
          content: "Write a professional email for...",
          category_id: "business",
          status: "published",
          is_featured: false,
          is_active: true,
          image_url: "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop",
          likes_count: 45,
          created_by: "admin",
          created_at: "2024-01-15T00:00:00Z",
          updated_at: "2024-01-15T00:00:00Z",
        };
        setPrompts([mockPrompt]);
        setCategories([{ id: "all", name: "All", order: 0, is_active: true, prompts_count: 1, created_at: "2024-01-15T00:00:00Z", updated_at: "2024-01-15T00:00:00Z" }]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [currentPage, searchTerm, selectedCategory]);

  // Handle search with debouncing
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      setCurrentPage(1); // Reset to first page when searching
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchTerm]);

  const handleDeletePrompt = async (promptId: string, promptTitle: string) => {
    if (confirm(`Are you sure you want to delete "${promptTitle}"? This action cannot be undone.`)) {
      try {
        await promptApi.deletePrompt(promptId);
        // Refresh the prompts list
        setPrompts(prevPrompts => prevPrompts.filter(p => p.id !== promptId));
        setTotalPrompts(prev => prev - 1);
      } catch (error) {
        console.error("Failed to delete prompt:", error);
        alert("Failed to delete prompt. Please try again.");
      }
    }
  };

  const handleFeatureToggle = async (promptId: string, isCurrentlyFeatured: boolean) => {
    try {
      if (isCurrentlyFeatured) {
        await promptApi.unfeaturePrompt(promptId);
      } else {
        await promptApi.featurePrompt(promptId);
      }
      
      // Update local state
      setPrompts(prevPrompts =>
        prevPrompts.map(p =>
          p.id === promptId ? { ...p, is_featured: !isCurrentlyFeatured } : p
        )
      );
    } catch (error) {
      console.error("Failed to toggle feature status:", error);
      alert("Failed to update feature status. Please try again.");
    }
  };

  const allCategories = [{ id: "all", name: "All" }, ...categories];

  return (
    <div>
      <ComponentCard
        title="All Prompts"
        desc="Manage and organize your prompts"
      >
      {/* Search and Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
        
        <div className="relative flex-1 max-w-md">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <SearchIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            placeholder="Search prompts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-brand-500 focus:border-brand-500 sm:text-sm dark:bg-gray-900 dark:border-gray-700 dark:text-white"
          />
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          {/* Category Filter */}
          <div className="relative">
            <Button
              variant="outline"
              onClick={() => setIsCategoryDropdownOpen(!isCategoryDropdownOpen)}
              className="flex items-center gap-2"
            >
              {selectedCategory}
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </Button>
            <Dropdown
              isOpen={isCategoryDropdownOpen}
              onClose={() => setIsCategoryDropdownOpen(false)}
              className="w-48"
            >
              {allCategories.map((category) => (
                <DropdownItem
                  key={category.id}
                  onClick={() => {
                    setSelectedCategory(category.id === "all" ? "All" : category.id);
                    setIsCategoryDropdownOpen(false);
                  }}
                >
                  {category.name}
                </DropdownItem>
              ))}
            </Dropdown>
          </div>


          <Button
            startIcon={<PlusIcon />}
            className="flex items-center gap-2 whitespace-nowrap"
            onClick={() => router.push('/prompts/add')}
          >
            <span className="hidden sm:inline">Add New Prompt</span>
            <span className="sm:hidden">Add</span>
          </Button>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500"></div>
          <span className="ml-2 text-gray-600 dark:text-gray-400">Loading prompts...</span>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20">
          <p className="text-red-600 dark:text-red-400">Failed to load prompts: {error}</p>
        </div>
      )}

      {/* Table */}
      {!loading && !error && (
        <div>
          <div className="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
            <div className="overflow-x-auto">
              <Table>
              <TableHeader className="border-b border-gray-100 dark:border-gray-800">
                <TableRow className="bg-gray-50 dark:bg-gray-800">
                  <TableCell
                    isHeader
                    className="px-4 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400 w-1/2 min-w-[300px]"
                  >
                    Prompt
                  </TableCell>
                  <TableCell
                    isHeader
                    className="px-4 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400 w-24"
                  >
                    Category
                  </TableCell>
                  <TableCell
                    isHeader
                    className="px-4 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400 w-20"
                  >
                    Likes
                  </TableCell>
                  <TableCell
                    isHeader
                    className="px-4 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400 w-24"
                  >
                    Created
                  </TableCell>
                  <TableCell
                    isHeader
                    className="px-4 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400 w-20"
                  >
                    Actions
                  </TableCell>
                </TableRow>
              </TableHeader>
              <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
                {prompts.map((prompt) => (
                  <TableRow key={prompt.id} className="bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800">
                    <TableCell className="px-4 py-3 text-start w-1/2 min-w-[300px]">
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-10 h-10 overflow-hidden rounded-lg flex-shrink-0 cursor-pointer hover:opacity-80 transition-opacity"
                          onClick={() => setPreviewModal({
                            isOpen: true,
                            imageUrl: prompt.image_url,
                            title: prompt.title
                          })}
                        >
                          <Image
                            {...getImageDimensions('prompt')}
                            src={getFullImageUrl(prompt.image_url)}
                            alt={prompt.title}
                            className="w-full h-full object-cover"
                          />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="block font-medium text-gray-800 text-theme-sm dark:text-white truncate">
                              {prompt.title}
                            </span>
                            {prompt.is_featured && (
                              <Badge color="warning" size="sm">Featured</Badge>
                            )}
                          </div>
                          <span className="block text-gray-500 text-theme-xs dark:text-gray-400 truncate">
                            {prompt.content.substring(0, 40)}...
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="px-4 py-3 text-start w-24">
                      <Badge color="primary" size="sm">
                        {getCategoryName(prompt.category_id)}
                      </Badge>
                    </TableCell>
                    <TableCell className="px-4 py-3 text-gray-500 text-theme-sm dark:text-gray-400 w-20 text-center">
                      {prompt.likes_count || 0}
                    </TableCell>
                    <TableCell className="px-4 py-3 text-gray-500 text-theme-sm dark:text-gray-400 w-24">
                      {new Date(prompt.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </TableCell>
                    <TableCell className="px-4 py-3 text-start w-20">
                      <div className="flex items-center gap-2">
                        <button 
                          onClick={() => handleFeatureToggle(prompt.id, prompt.is_featured)}
                          className={`p-1 transition-colors ${prompt.is_featured 
                            ? 'text-yellow-500 hover:text-yellow-600' 
                            : 'text-gray-500 hover:text-yellow-500 dark:text-gray-400'}`}
                          title={prompt.is_featured ? "Remove from featured" : "Mark as featured"}
                        >
                          ⭐
                        </button>
                        <button 
                          onClick={() => router.push(`/prompts/edit/${prompt.id}`)}
                          className="p-1 text-gray-500 hover:text-brand-500 dark:text-gray-400 dark:hover:text-brand-400 transition-colors"
                          title="Edit prompt"
                        >
                          <PencilIcon className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handleDeletePrompt(prompt.id, prompt.title)}
                          className="p-1 text-gray-500 hover:text-error-500 dark:text-gray-400 dark:hover:text-error-400 transition-colors"
                          title="Delete prompt"
                        >
                          <TrashBinIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
              </Table>
            </div>
          </div>

          {/* Summary */}
          <div className="flex items-center justify-between pt-4">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Showing {prompts.length} of {totalPrompts} prompts
            </div>
            {totalPrompts > pageSize && (
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Page {currentPage} of {Math.ceil(totalPrompts / pageSize)}
                </span>
                <button
                  onClick={() => setCurrentPage(prev => prev + 1)}
                  disabled={currentPage >= Math.ceil(totalPrompts / pageSize)}
                  className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </ComponentCard>

    {/* Image Preview Modal */}
    <ImagePreviewModal
      isOpen={previewModal.isOpen}
      onClose={() => setPreviewModal({ isOpen: false })}
      imageUrl={previewModal.imageUrl}
      title={previewModal.title}
      alt="Prompt Image"
    />
  </div>
  );
}
