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
import { PencilIcon, TrashBinIcon, PlusIcon, FolderIcon, SearchIcon } from "@/icons";
import ComponentCard from "../common/ComponentCard";
import { categoryApi, CategoryAdmin } from "@/services";

interface Category {
  id: string;
  name: string;
  description?: string;
  prompt_count: number;
  order: number;
  color: string;
  created_at: string;
  is_active: boolean;
}

export default function CategoriesTable() {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState("");
  const [categories, setCategories] = useState<CategoryAdmin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCategories, setTotalCategories] = useState(0);
  const pageSize = 10;

  // Fetch categories from API
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        setLoading(true);
        
        const categoriesResponse = await categoryApi.getCategories({
          page: currentPage,
          limit: pageSize,
          search: searchTerm || undefined,
        });
        
        setCategories(categoriesResponse.items || []);
        setTotalCategories(categoriesResponse.total || 0);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch categories:", err);
        setError(err instanceof Error ? err.message : "Failed to load categories");
        
        // Fallback to static categories
        const staticCategories: Category[] = [
          {
            id: "1",
            name: "New",
            description: "Latest prompts",
            prompt_count: 25,
            order: 1,
            color: "#3B82F6",
            created_at: "2024-01-15",
            is_active: true,
          },
          {
            id: "2",
            name: "Trending",
            description: "Popular prompts",
            prompt_count: 18,
            order: 2,
            color: "#EF4444",
            created_at: "2024-01-15",
            is_active: true,
          },
        ];
        setCategories(staticCategories);
        setTotalCategories(staticCategories.length);
      } finally {
        setLoading(false);
      }
    };

    fetchCategories();
  }, [currentPage, searchTerm]);

  // Handle search with debouncing
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      setCurrentPage(1); // Reset to first page when searching
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchTerm]);

  const handleDeleteCategory = async (categoryId: string, categoryName: string) => {
    if (confirm(`Are you sure you want to delete "${categoryName}"? This action cannot be undone and will affect all prompts in this category.`)) {
      try {
        await categoryApi.deleteCategory(categoryId);
        // Refresh the categories list
        setCategories(prevCategories => prevCategories.filter(c => c.id !== categoryId));
        setTotalCategories(prev => prev - 1);
      } catch (error) {
        console.error("Failed to delete category:", error);
        alert("Failed to delete category. Please try again.");
      }
    }
  };

  const handleStatusToggle = async (categoryId: string, isCurrentlyActive: boolean) => {
    try {
      await categoryApi.toggleStatus(categoryId);
      
      // Update local state
      setCategories(prevCategories =>
        prevCategories.map(c =>
          c.id === categoryId ? { ...c, is_active: !isCurrentlyActive } : c
        )
      );
    } catch (error) {
      console.error("Failed to toggle category status:", error);
      alert("Failed to update category status. Please try again.");
    }
  };

  return (
    <ComponentCard
      title="All Categories"
      desc="Manage and organize your prompt categories"
    >
      {/* Search and Actions */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
        <div className="relative flex-1 max-w-md">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <SearchIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            placeholder="Search categories..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-brand-500 focus:border-brand-500 sm:text-sm dark:bg-gray-900 dark:border-gray-700 dark:text-white"
          />
        </div>

        <Button
          startIcon={<PlusIcon />}
          className="flex items-center gap-2"
          onClick={() => router.push('/categories/add')}
        >
          Add Category
        </Button>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500"></div>
          <span className="ml-2 text-gray-600 dark:text-gray-400">Loading categories...</span>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20">
          <p className="text-red-600 dark:text-red-400">Failed to load categories: {error}</p>
        </div>
      )}

      {/* Table */}
      {!loading && !error && (
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
                      Category
                    </TableCell>
                    <TableCell
                      isHeader
                      className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400"
                    >
                      Prompts
                    </TableCell>
                    <TableCell
                      isHeader
                      className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400"
                    >
                      Order
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
                      Created
                    </TableCell>
                    <TableCell
                      isHeader
                      className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400"
                    >
                      Actions
                    </TableCell>
                  </TableRow>
                </TableHeader>
                <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {categories.map((category) => (
                    <TableRow key={category.id} className="bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800">
                      <TableCell className="px-5 py-4 sm:px-6 text-start">
                        <div className="flex items-center gap-3">
                          <div 
                            className="w-10 h-10 rounded-lg flex items-center justify-center"
                            style={{ backgroundColor: category.color || "#465fff" }}
                          >
                            <FolderIcon className="w-5 h-5 text-white" />
                          </div>
                          <div>
                            <span className="block font-medium text-gray-800 text-theme-sm dark:text-white">
                              {category.name}
                            </span>
                            <span className="block text-gray-500 text-theme-xs dark:text-gray-400">
                              {category.description || `Color: ${category.color || "#465fff"}`}
                            </span>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="px-4 py-3 text-start">
                        <Badge color="primary" size="sm">
                            {category.prompts_count} prompts
                        </Badge>
                      </TableCell>
                      <TableCell className="px-4 py-3 text-gray-500 text-theme-sm dark:text-gray-400">
                        #{category.order}
                      </TableCell>
                      <TableCell className="px-4 py-3 text-start">
                        <div className="flex items-center gap-2">
                          <Badge
                            color={category.is_active ? "success" : "error"}
                            size="sm"
                          >
                            {category.is_active ? "Active" : "Inactive"}
                          </Badge>
                          <button 
                            onClick={() => handleStatusToggle(category.id, category.is_active)}
                            className="p-1 text-gray-500 hover:text-brand-500 dark:text-gray-400 dark:hover:text-brand-400 transition-colors"
                            title={category.is_active ? "Deactivate category" : "Activate category"}
                          >
                            {category.is_active ? "🔽" : "🔼"}
                          </button>
                        </div>
                      </TableCell>
                      <TableCell className="px-4 py-3 text-gray-500 text-theme-sm dark:text-gray-400">
                        {new Date(category.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="px-4 py-3 text-start">
                        <div className="flex items-center gap-2">
                          <button 
                            onClick={() => router.push(`/categories/edit/${category.id}`)}
                            className="p-1 text-gray-500 hover:text-brand-500 dark:text-gray-400 dark:hover:text-brand-400 transition-colors"
                            title="Edit category"
                          >
                            <PencilIcon className="w-4 h-4" />
                          </button>
                          <button 
                            onClick={() => handleDeleteCategory(category.id, category.name)}
                            className="p-1 text-gray-500 hover:text-error-500 dark:text-gray-400 dark:hover:text-error-400 transition-colors"
                            title="Delete category"
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
        </div>
      )}

      {/* Summary */}
      <div className="flex items-center justify-between pt-4">
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Showing {categories.length} of {totalCategories} categories
        </div>
        {totalCategories > pageSize && !searchTerm && (
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Page {currentPage} of {Math.ceil(totalCategories / pageSize)}
            </span>
            <button
              onClick={() => setCurrentPage(prev => prev + 1)}
              disabled={currentPage >= Math.ceil(totalCategories / pageSize)}
              className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        )}
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Total Prompts: {categories.reduce((sum, cat) => sum + cat.prompt_count, 0)}
        </div>
      </div>
    </ComponentCard>
  );
}
