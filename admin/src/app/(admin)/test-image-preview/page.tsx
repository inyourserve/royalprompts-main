"use client";
import React from "react";
import ComponentCard from "@/components/common/ComponentCard";
import PageHeader from "@/components/common/PageHeader";
import ImagePreviewDemo from "@/components/common/ImagePreviewDemo";

export default function TestImagePreviewPage() {
  return (
    <div className="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10">
      <PageHeader 
        title="Image Preview Test"
        description="Test the image preview functionality with your MongoDB document"
      />
      
      <div className="grid grid-cols-1 gap-6">
        <ComponentCard title="Image Preview Demo">
          <ImagePreviewDemo />
        </ComponentCard>

        <ComponentCard title="Test with Different URLs">
          <div className="space-y-6">
            <ImagePreviewDemo 
              imageUrl="/uploads/images/441bc457-5db8-4a9d-b4a7-244eb42da542.png"
              title="Your MongoDB Document Image"
            />
            
            <ImagePreviewDemo 
              imageUrl="https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop"
              title="External URL Test"
            />
            
            <ImagePreviewDemo 
              imageUrl=""
              title="Empty URL Test (Should show fallback)"
            />
          </div>
        </ComponentCard>

        <ComponentCard title="Implementation Details">
          <div className="space-y-4 text-sm text-gray-600 dark:text-gray-300">
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                What was implemented:
              </h4>
              <ul className="list-disc list-inside space-y-1 ml-4">
                <li>Added <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">getFullImageUrl()</code> utility function</li>
                <li>Updated PromptsTable component to use full image URLs</li>
                <li>Updated RecentPrompts component to use full image URLs</li>
                <li>Updated FileUploadWithPreview component to handle full URLs</li>
                <li>Created ImagePreviewModal component for full-size image viewing</li>
                <li>Made images clickable to open preview modal</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                How it works:
              </h4>
              <ul className="list-disc list-inside space-y-1 ml-4">
                <li>Relative URLs like <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">/uploads/images/...</code> are converted to full URLs</li>
                <li>Full URLs (starting with http/https) are used as-is</li>
                <li>Empty or null URLs fall back to a default image</li>
                <li>Images are clickable and open in a modal for full-size viewing</li>
              </ul>
            </div>
          </div>
        </ComponentCard>
      </div>
    </div>
  );
}
