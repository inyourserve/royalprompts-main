"use client";
import React, { useState } from "react";
import { getFullImageUrl } from "@/utils/image";
import ImagePreviewModal from "./ImagePreviewModal";

interface ImagePreviewDemoProps {
  imageUrl?: string;
  title?: string;
}

export default function ImagePreviewDemo({ 
  imageUrl = "/uploads/images/441bc457-5db8-4a9d-b4a7-244eb42da542.png",
  title = "Sample Prompt"
}: ImagePreviewDemoProps) {
  const [previewModal, setPreviewModal] = useState<{
    isOpen: boolean;
    imageUrl?: string;
    title?: string;
  }>({ isOpen: false });

  const fullImageUrl = getFullImageUrl(imageUrl);

  return (
    <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Image Preview Demo
      </h3>
      
      <div className="space-y-4">
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
            <strong>Original URL:</strong> {imageUrl}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
            <strong>Full URL:</strong> {fullImageUrl}
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div 
            className="w-20 h-20 overflow-hidden rounded-lg cursor-pointer hover:opacity-80 transition-opacity border border-gray-200 dark:border-gray-600"
            onClick={() => setPreviewModal({
              isOpen: true,
              imageUrl: imageUrl,
              title: title
            })}
          >
            <img
              src={fullImageUrl}
              alt={title}
              className="w-full h-full object-cover"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop';
              }}
            />
          </div>
          
          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-white">
              {title}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Click image to preview
            </p>
          </div>
        </div>

        <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <p className="text-xs text-gray-600 dark:text-gray-300">
            <strong>Test URL:</strong> This demo uses the image URL from your MongoDB document: 
            <code className="ml-1 px-1 py-0.5 bg-gray-200 dark:bg-gray-600 rounded text-xs">
              /uploads/images/441bc457-5db8-4a9d-b4a7-244eb42da542.png
            </code>
          </p>
        </div>
      </div>

      {/* Image Preview Modal */}
      <ImagePreviewModal
        isOpen={previewModal.isOpen}
        onClose={() => setPreviewModal({ isOpen: false })}
        imageUrl={previewModal.imageUrl}
        title={previewModal.title}
        alt="Demo Image"
      />
    </div>
  );
}
