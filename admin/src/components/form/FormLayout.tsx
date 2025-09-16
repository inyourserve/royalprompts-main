"use client";
import React from "react";
import { useRouter } from "next/navigation";
import Button from "../ui/button/Button";
import Alert from "../ui/alert/Alert";

interface FormLayoutProps {
  title?: string;
  description?: string;
  children: React.ReactNode;
  onSubmit?: (e: React.FormEvent) => void;
  isLoading?: boolean;
  isSuccess?: boolean;
  successTitle?: string;
  successMessage?: string;
  submitButtonText?: string;
  cancelButtonText?: string;
  showDeleteButton?: boolean;
  onDelete?: () => void;
  isDeleting?: boolean;
  deleteButtonText?: string;
  className?: string;
}

export default function FormLayout({
  title,
  description,
  children,
  onSubmit,
  isLoading = false,
  isSuccess = false,
  successTitle = "Success!",
  successMessage = "Operation completed successfully.",
  submitButtonText = "Save",
  cancelButtonText = "Cancel",
  showDeleteButton = false,
  onDelete,
  isDeleting = false,
  deleteButtonText = "Delete",
  className = "",
}: FormLayoutProps) {
  const router = useRouter();

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header - Only show if title is provided */}
      {title && (
        <div>
          <h2 className="text-2xl font-bold text-gray-800 dark:text-white">
            {title}
          </h2>
          {description && (
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              {description}
            </p>
          )}
        </div>
      )}

      {/* Success Alert */}
      {isSuccess && (
        <Alert 
          variant="success" 
          title={successTitle}
          message={successMessage}
        />
      )}

      {/* Form */}
      <form onSubmit={onSubmit} className="space-y-6">
        {children}

        {/* Action Buttons */}
        <div className="flex gap-4 pt-6 border-t border-gray-200 dark:border-gray-700">
          <Button
            type="submit"
            variant="primary"
            disabled={isLoading}
            className="flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                {submitButtonText}...
              </>
            ) : (
              submitButtonText
            )}
          </Button>
          
          <Button
            type="button"
            variant="outline"
            onClick={() => router.back()}
            disabled={isLoading || isDeleting}
          >
            {cancelButtonText}
          </Button>

          {showDeleteButton && onDelete && (
            <Button
              type="button"
              variant="outline"
              onClick={onDelete}
              disabled={isLoading || isDeleting}
              className="flex items-center gap-2 ml-auto border-red-500 text-red-500 hover:bg-red-50 dark:border-red-400 dark:text-red-400 dark:hover:bg-red-900/20"
            >
              {isDeleting ? (
                <>
                  <div className="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
                  Deleting...
                </>
              ) : (
                deleteButtonText
              )}
            </Button>
          )}
        </div>
      </form>
    </div>
  );
}
