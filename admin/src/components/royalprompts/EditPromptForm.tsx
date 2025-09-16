"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import FormLayout from "../form/FormLayout";
import FormField from "../form/FormField";
import FormCheckbox from "../form/FormCheckbox";
import TagInput from "../form/TagInput";
import FileUploadWithPreview from "../form/FileUploadWithPreview";
import { promptApi, PromptUpdate, categoryApi } from "@/services";
import { CategoryAdmin } from "@/types";

interface PromptFormData {
  title: string;
  description: string;
  content: string;
  category_id: string;
  status: 'draft' | 'published';
  is_featured: boolean;
  is_active: boolean;
  image_url?: string;
  image: File | null;
}

interface EditPromptFormProps {
  promptId: string;
}

export default function EditPromptForm({ promptId }: EditPromptFormProps) {
  const router = useRouter();
  const [formData, setFormData] = useState<PromptFormData>({
    title: "",
    description: "",
    content: "",
    category_id: "",
    status: "published",
    is_featured: false,
    is_active: true,
    image_url: "",
    image: null,
  });

  const [categories, setCategories] = useState<CategoryAdmin[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoadingData, setIsLoadingData] = useState(true);

  // Load prompt data and categories
  useEffect(() => {
    const loadData = async () => {
      setIsLoadingData(true);
      
      try {
        // Load prompt data and categories in parallel
        const [prompt, categoriesResponse] = await Promise.all([
          promptApi.getPromptById(promptId),
          categoryApi.getCategories({ limit: 100 })
        ]);

        setFormData({
          title: prompt.title,
          description: prompt.description,
          content: prompt.content,
          category_id: prompt.category_id,
          status: prompt.status,
          is_featured: prompt.is_featured,
          is_active: prompt.is_active,
          image_url: prompt.image_url || "",
          image: null,
        });

        setCategories(categoriesResponse.items);
      } catch (error) {
        console.error("Error loading prompt data:", error);
        // Prompt not found, redirect to prompts list
        router.push("/prompts");
        return;
      }
      
      setIsLoadingData(false);
    };

    loadData();
  }, [promptId, router]);

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

    if (!formData.category_id.trim()) {
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
      let imageUrl = formData.image_url;
      
      // Upload new image if selected
      if (formData.image) {
        const uploadResponse = await promptApi.uploadImage(formData.image);
        imageUrl = uploadResponse.url;
      }

      const updateData: PromptUpdate = {
        title: formData.title,
        description: formData.description,
        content: formData.content,
        category_id: formData.category_id,
        status: formData.status,
        is_featured: formData.is_featured,
        is_active: formData.is_active,
        image_url: imageUrl
      };
      
      await promptApi.updatePrompt(promptId, updateData);
      
      setIsLoading(false);
      setIsSuccess(true);
      
      // Redirect after success
      setTimeout(() => {
        router.push("/prompts");
      }, 2000);
    } catch (error) {
      console.error("Error updating prompt:", error);
      setIsLoading(false);
      // Handle error (show error message, etc.)
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this prompt? This action cannot be undone.")) {
      return;
    }

    setIsDeleting(true);
    
    try {
      await promptApi.deletePrompt(promptId);
      
      setIsDeleting(false);
      
      // Redirect to prompts list
      router.push("/prompts");
    } catch (error) {
      console.error("Error deleting prompt:", error);
      setIsDeleting(false);
    }
  };

  if (isLoadingData || categories.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading prompt data...</p>
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
      successTitle="Prompt Updated Successfully!"
      successMessage="Your prompt has been updated and saved."
      submitButtonText="Update Prompt"
      showDeleteButton={true}
      onDelete={handleDelete}
      isDeleting={isDeleting}
      deleteButtonText="Delete Prompt"
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

        {/* Category */}
        <div>
          <FormField
            label="Category"
            name="category_id"
            type="select"
            placeholder="Select a category"
            value={formData.category_id}
            onSelectChange={(value) => handleInputChange("category_id", value)}
            options={categoryOptions}
            required
            error={errors.category_id}
          />
        </div>

        {/* Status */}
        <div>
          <FormField
            label="Status"
            name="status"
            type="select"
            placeholder="Select status"
            value={formData.status}
            onSelectChange={(value) => handleInputChange("status", value)}
            options={[
              { value: "published", label: "Published" },
              { value: "draft", label: "Draft" }
            ]}
            required
          />
        </div>
      </div>

      {/* Description */}
      <FormField
        label="Description"
        name="description"
        type="textarea"
        placeholder="Enter prompt description..."
        value={formData.description}
        onChange={(value) => handleInputChange("description", value as string)}
        rows={3}
        required
        error={errors.description}
      />

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
      <FileUploadWithPreview
        label="Prompt Image (Optional)"
        name="image"
        accept="image/*"
        maxSize={5}
        onFileSelect={handleFileSelect}
        selectedFile={formData.image}
        currentImageUrl={formData.image_url}
      />

      {/* Feature Toggles */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <FormCheckbox
          id="is_featured"
          label="Featured Prompt"
          checked={formData.is_featured}
          onChange={(checked) => handleInputChange("is_featured", checked)}
        />
        
        <FormCheckbox
          id="is_active"
          label="Active (visible to users)"
          checked={formData.is_active}
          onChange={(checked) => handleInputChange("is_active", checked)}
        />
      </div>
    </FormLayout>
  );
}