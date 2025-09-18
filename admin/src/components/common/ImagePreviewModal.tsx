"use client";
import React from "react";
import { CloseIcon } from "@/icons";
import { getFullImageUrl } from "@/utils/image";

interface ImagePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageUrl?: string | null;
  title?: string;
  alt?: string;
}

export default function ImagePreviewModal({
  isOpen,
  onClose,
  imageUrl,
  title = "Image Preview",
  alt = "Preview"
}: ImagePreviewModalProps) {
  if (!isOpen || !imageUrl) return null;

  const fullImageUrl = getFullImageUrl(imageUrl);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-75"
        onClick={onClose}
      />
      
      {/* Modal Content */}
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {title}
          </h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <CloseIcon className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </button>
        </div>
        
        {/* Image */}
        <div className="p-4">
          <div className="relative max-h-[70vh] overflow-hidden rounded-lg">
            <img
              src={fullImageUrl}
              alt={alt}
              className="w-full h-auto max-h-[70vh] object-contain"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = '/images/error/image-not-found.svg';
              }}
            />
          </div>
          
          {/* Image URL Info */}
          <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">
              <strong>Image URL:</strong>
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 break-all">
              {fullImageUrl}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
