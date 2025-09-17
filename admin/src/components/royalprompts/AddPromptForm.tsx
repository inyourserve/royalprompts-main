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
  tempImageUrl: string | null;
  tempImageFilename: string | null;
  finalImageUrl: string | null;
  finalImageFilename: string | null;
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
    tempImageUrl: null,
    tempImageFilename: null,
    finalImageUrl: null,
    finalImageFilename: null,
  });

  const [categories, setCategories] = useState<CategoryAdmin[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoadingCategories, setIsLoadingCategories] = useState(true);
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

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


  const handleFileSelect = async (file: File | null) => {
    if (!file) {
      setFormData(prev => ({
        ...prev,
        image: null,
        tempImageUrl: null,
        tempImageFilename: null,
        finalImageUrl: null,
        finalImageFilename: null,
      }));
      return;
    }

    setFormData(prev => ({
      ...prev,
      image: file,
    }));

    // Upload temp image for preview when file is selected
    setIsUploadingImage(true);
    setUploadProgress(0);
    
    try {
      // Simulate progress (since we can't get real progress from fetch)
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 100);

      const uploadResponse = await promptApi.uploadTempImage(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      // Store the temp upload response
      setFormData(prev => ({
        ...prev,
        tempImageUrl: uploadResponse.url,
        tempImageFilename: uploadResponse.filename,
      }));
      
      // Clear any previous errors
      if (errors.image) {
        setErrors(prev => ({
          ...prev,
          image: ""
        }));
      }
      
    } catch (error) {
      console.error("Error uploading temp image:", error);
      setErrors(prev => ({
        ...prev,
        image: "Failed to upload image. Please try again."
      }));
      
      // Reset form data on upload failure
      setFormData(prev => ({
        ...prev,
        image: null,
        tempImageUrl: null,
        tempImageFilename: null,
      }));
    } finally {
      setIsUploadingImage(false);
      setUploadProgress(0);
    }
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

    // Check if image is selected but not uploaded yet
    if (formData.image && !formData.tempImageUrl) {
      newErrors.image = "Please wait for image upload to complete";
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
      let finalImageUrl = null;
      
      // Upload final image if temp image exists
      if (formData.tempImageUrl && formData.image) {
        const finalUploadResponse = await promptApi.uploadImage(formData.image);
        finalImageUrl = finalUploadResponse.url;
        
        // Store final upload response
        setFormData(prev => ({
          ...prev,
          finalImageUrl: finalUploadResponse.url,
          finalImageFilename: finalUploadResponse.filename,
        }));
      }
      
      // Create prompt data using the final uploaded image URL
      const promptData: PromptCreate = {
        title: formData.title,
        description: formData.description,
        content: formData.content,
        category_id: formData.category_id,
        is_featured: formData.is_featured,
        image_url: finalImageUrl || undefined,
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
      isLoading={isLoading || isUploadingImage}
      isSuccess={isSuccess}
      successTitle="Prompt Created Successfully!"
      successMessage="Your new prompt has been added to the collection."
      submitButtonText={isUploadingImage ? "Uploading Image..." : "Create Prompt"}
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
        isUploading={isUploadingImage}
        uploadProgress={uploadProgress}
        uploadedImageUrl={formData.tempImageUrl}
        error={errors.image}
      />

    </FormLayout>
  );
}
