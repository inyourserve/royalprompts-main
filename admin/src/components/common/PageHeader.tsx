"use client";
import React from "react";
import { useRouter } from "next/navigation";
import { ChevronLeftIcon } from "@/icons";

interface PageHeaderProps {
  title: string;
  description?: string;
  showBackButton?: boolean;
  backButtonText?: string;
  className?: string;
}

export default function PageHeader({
  title,
  description,
  showBackButton = true,
  backButtonText = "Back",
  className = "",
}: PageHeaderProps) {
  const router = useRouter();

  return (
    <div className={`mb-6 ${className}`}>
      {showBackButton && (
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 transition-colors mb-4"
        >
          <ChevronLeftIcon className="w-4 h-4" />
          {backButtonText}
        </button>
      )}
      
      <div>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
          {title}
        </h1>
        {description && (
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            {description}
          </p>
        )}
      </div>
    </div>
  );
}
