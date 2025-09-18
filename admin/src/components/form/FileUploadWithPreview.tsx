"use client";
import React, { useState, useRef } from "react";
import Label from "./Label";
import Button from "../ui/button/Button";
import { PlusIcon, CloseIcon } from "@/icons";
import { getFullImageUrl } from "@/utils/image";

interface FileUploadWithPreviewProps {
  label: string;
  name: string;
  accept?: string;
  maxSize?: number; // in MB
  onFileSelect: (file: File | null) => void;
  selectedFile?: File | null;
  currentImageUrl?: string; // For existing images
  required?: boolean;
  error?: string;
  className?: string;
}

export default function FileUploadWithPreview({
  label,
  name,
  accept = "image/*",
  maxSize = 5, // 5MB default
  onFileSelect,
  selectedFile,
  currentImageUrl,
  required = false,
  error,
  className = "",
}: FileUploadWithPreviewProps) {
  const [dragActive, setDragActive] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const hasError = !!error;

  const handleFile = (file: File) => {
    // Validate file size
    if (file.size > maxSize * 1024 * 1024) {
      alert(`File size must be less than ${maxSize}MB`);
      return;
    }

    // Validate file type
    if (accept && !file.type.match(accept.replace(/\*/g, ".*"))) {
      alert(`Please select a valid file type. Accepted: ${accept}`);
      return;
    }

    onFileSelect(file);

    // Create preview URL
    if (file.type.startsWith("image/")) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const removeFile = () => {
    onFileSelect(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  // Determine what image to show
  const displayImage = previewUrl || getFullImageUrl(currentImageUrl);
  const hasImage = selectedFile || currentImageUrl;

  return (
    <div className={className}>
      <Label htmlFor={name}>
        {label}
        {required && <span className="text-error-500 ml-1">*</span>}
      </Label>

      <div
        className={`relative border-2 border-dashed rounded-lg p-6 transition-colors ${
          dragActive
            ? "border-brand-500 bg-brand-50 dark:bg-brand-900/20"
            : hasError
            ? "border-error-500 bg-error-50 dark:bg-error-900/20"
            : "border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500"
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          id={name}
          name={name}
          accept={accept}
          onChange={handleChange}
          className="hidden"
        />

        {hasImage ? (
          <div className="text-center">
            {displayImage && (
              <div className="mb-4">
                <img
                  src={displayImage}
                  alt="Preview"
                  className="max-h-48 mx-auto rounded-lg shadow-sm"
                />
                {currentImageUrl && !selectedFile && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    Current image
                  </p>
                )}
                {selectedFile && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    New image: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                )}
              </div>
            )}
            
            <div className="flex gap-2 justify-center">
              <Button
                variant="outline"
                onClick={openFileDialog}
                className="flex items-center gap-2"
              >
                <PlusIcon className="w-4 h-4" />
                {selectedFile ? "Change Image" : "Upload New Image"}
              </Button>
              
              <Button
                variant="outline"
                onClick={removeFile}
                className="flex items-center gap-2"
              >
                <CloseIcon className="w-4 h-4" />
                Remove
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center">
            <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
              <PlusIcon className="w-8 h-8 text-gray-400" />
            </div>
            
            <p className="text-sm font-medium text-gray-900 dark:text-white mb-1">
              Drop your image here, or{" "}
              <button
                onClick={openFileDialog}
                className="text-brand-500 hover:text-brand-600 dark:text-brand-400 dark:hover:text-brand-300 underline"
              >
                browse
              </button>
            </p>
            
            <p className="text-xs text-gray-500 dark:text-gray-400">
              PNG, JPG, GIF up to {maxSize}MB
            </p>
          </div>
        )}
      </div>

      {hasError && (
        <p className="text-error-500 text-sm mt-1">{error}</p>
      )}
    </div>
  );
}
