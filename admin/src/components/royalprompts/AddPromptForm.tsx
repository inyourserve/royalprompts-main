"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import FormLayout from "../form/FormLayout";
import FormField from "../form/FormField";
import FormCheckbox from "../form/FormCheckbox";
import FileUpload from "../form/FileUpload";
import { promptApi, PromptCreate, categoryApi, CategoryAdmin } from "@/services";

interface PromptFormData {
  title: string;
  description: string;
  content: string;
  category_id: string;
  is_featured: boolean;
  image: File | null;
}

export default function AddPromptForm() {
  const router = useRouter();
  const [formData, setFormData] = useState<PromptFormData>({
    title: "",
    description: "",
    content: "",
    category_id: "",
    is_featured: false,
    image: null,
  });

  const [categories, setCategories] = useState<CategoryAdmin[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoadingCategories, setIsLoadingCategories] = useState(true);

  // Load categories
  useEffect(() => {
    const loadCategories = async () => {
      try {
        setIsLoadingCategories(true);
        const categoriesResponse = await categoryApi.getCategories({ limit: 100 });
        setCategories(categoriesResponse.items);
      } catch (error) {
        console.error("Error loading categories:", error);
      } finally {
        setIsLoadingCategories(false);
      }
    };

    loadCategories();
  }, []);

  const handleInputChange = (field: keyof PromptFormData, value: string | boolean) => {
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


  const handleFileSelect = (file: File | null) => {
    setFormData(prev => ({
      ...prev,
      image: file
    }));
  };


  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = "Title is required";
    }

    if (!formData.description.trim()) {
      newErrors.description = "Description is required";
    }

    if (!formData.category_id) {
      newErrors.category_id = "Category is required";
    }

    if (!formData.content.trim()) {
      newErrors.content = "Prompt content is required";
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
      let imageUrl = null;
      
      // Upload image first if provided
      if (formData.image) {
        const uploadResponse = await promptApi.uploadImage(formData.image);
        imageUrl = uploadResponse.url;
      }
      
      // Create prompt data
      const promptData: PromptCreate = {
        title: formData.title,
        description: formData.description,
        content: formData.content,
        category_id: formData.category_id,
        is_featured: formData.is_featured,
        image_url: imageUrl || undefined,
      };
      
      // Create the prompt
      await promptApi.createPrompt(promptData);
      
      setIsLoading(false);
      setIsSuccess(true);
      
      // Redirect after success
      setTimeout(() => {
        router.push("/prompts");
      }, 2000);
    } catch (error) {
      console.error("Error submitting form:", error);
      setIsLoading(false);
      // Handle error (show error message, etc.)
    }
  };

  if (isLoadingCategories || categories.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading categories...</p>
        </div>
      </div>
    );
  }

  const categoryOptions = categories.map(cat => ({ value: cat.id, label: cat.name }));

  return (
    <FormLayout
      onSubmit={handleSubmit}
      isLoading={isLoading}
      isSuccess={isSuccess}
      successTitle="Prompt Created Successfully!"
      successMessage="Your new prompt has been added to the collection."
      submitButtonText="Create Prompt"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Title */}
        <div className="md:col-span-2">
          <FormField
            label="Prompt Title"
            name="title"
            type="text"
            placeholder="Enter prompt title"
            value={formData.title}
            onChange={(value) => handleInputChange("title", value as string)}
            required
            error={errors.title}
          />
        </div>

        {/* Description */}
        <div className="md:col-span-2">
          <FormField
            label="Description"
            name="description"
            type="textarea"
            placeholder="Enter a brief description of the prompt"
            value={formData.description}
            onChange={(value) => handleInputChange("description", value as string)}
            rows={3}
            error={errors.description}
          />
        </div>

        {/* Category */}
        <div>
          <FormField
            label="Category"
            name="category"
            type="select"
            placeholder="Select a category"
            value={formData.category_id}
            onSelectChange={(value) => handleInputChange("category_id", value)}
            options={categoryOptions}
            required
            error={errors.category_id}
          />
        </div>

        {/* Featured Toggle */}
        <div className="flex items-center">
          <FormCheckbox
            id="is_featured"
            label="Mark as Featured"
            checked={formData.is_featured}
            onChange={(checked) => handleInputChange("is_featured", checked)}
          />
        </div>
      </div>

      {/* Prompt Content */}
      <FormField
        label="Prompt Content"
        name="content"
        type="textarea"
        placeholder="Enter the full prompt content..."
        value={formData.content}
        onChange={(value) => handleInputChange("content", value as string)}
        rows={8}
        required
        error={errors.content}
      />

      {/* Image Upload */}
      <FileUpload
        label="Prompt Image (Optional)"
        name="image"
        accept="image/*"
        maxSize={5}
        onFileSelect={handleFileSelect}
        selectedFile={formData.image}
      />

    </FormLayout>
  );
}
