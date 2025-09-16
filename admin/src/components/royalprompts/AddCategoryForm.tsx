"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import FormLayout from "../form/FormLayout";
import FormField from "../form/FormField";
import FormCheckbox from "../form/FormCheckbox";
import { FolderIcon } from "@/icons";
import { categoryApi, CategoryCreate } from "@/services";

interface CategoryFormData {
  name: string;
  description: string;
  order: number;
  is_active: boolean;
  icon?: string;
  color?: string;
}


export default function AddCategoryForm() {
  const router = useRouter();
  const [formData, setFormData] = useState<CategoryFormData>({
    name: "",
    description: "",
    order: 1,
    is_active: true,
    icon: "",
    color: "#3B82F6",
  });

  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleInputChange = (field: keyof CategoryFormData, value: string | number | boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ""
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Category name is required";
    }

    if (!formData.description.trim()) {
      newErrors.description = "Description is required";
    }

    if (formData.order < 1) {
      newErrors.order = "Order must be at least 1";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    
    try {
      // Create the category via API
      const categoryData: CategoryCreate = {
        name: formData.name,
        description: formData.description,
        order: formData.order,
        is_active: formData.is_active,
        icon: formData.icon,
        color: formData.color,
      };
      
      await categoryApi.createCategory(categoryData);
      
      setIsLoading(false);
      setIsSuccess(true);
      
      // Redirect after success
      setTimeout(() => {
        router.push("/categories");
      }, 2000);
    } catch (error) {
      console.error("Failed to create category:", error);
      setIsLoading(false);
      alert("Failed to create category. Please try again.");
    }
  };

  return (
    <FormLayout
      onSubmit={handleSubmit}
      isLoading={isLoading}
      isSuccess={isSuccess}
      successTitle="Category Created Successfully!"
      successMessage="Your new category has been added to the system."
      submitButtonText="Create Category"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Category Name */}
        <div>
          <FormField
            label="Category Name"
            name="name"
            type="text"
            placeholder="Enter category name"
            value={formData.name}
            onChange={(value) => handleInputChange("name", value)}
            required
            error={errors.name}
          />
        </div>

        {/* Order */}
        <div>
          <FormField
            label="Display Order"
            name="order"
            type="number"
            placeholder="Enter display order"
            value={formData.order}
            onChange={(value) => handleInputChange("order", parseInt(value.toString()) || 1)}
            required
            error={errors.order}
            min={1}
          />
          <p className="text-gray-500 text-sm mt-1">
            Lower numbers appear first in the category list
          </p>
        </div>
      </div>

      {/* Description */}
      <FormField
        label="Description"
        name="description"
        type="textarea"
        placeholder="Enter category description..."
        value={formData.description}
        onChange={(value) => handleInputChange("description", value)}
        rows={4}
        required
        error={errors.description}
      />


      {/* Preview */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Preview
        </label>
        <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-brand-50 dark:bg-brand-500/20">
              <FolderIcon className="w-5 h-5 text-brand-500 dark:text-brand-400" />
            </div>
            <div>
              <h4 className="font-medium text-gray-800 dark:text-white/90">
                {formData.name || "Category Name"}
              </h4>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {formData.description || "Category description will appear here"}
              </p>
            </div>
            <div className="ml-auto">
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Order: {formData.order}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Active Toggle */}
      <FormCheckbox
        id="is_active"
        label="Category is active (visible to users)"
        checked={formData.is_active}
        onChange={(checked) => handleInputChange("is_active", checked)}
      />
    </FormLayout>
  );
}