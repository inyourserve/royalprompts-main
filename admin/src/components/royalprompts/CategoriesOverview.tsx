"use client";
import React from "react";
import { FolderIcon, PlusIcon, MoreDotIcon } from "@/icons";

interface Category {
  id: number;
  name: string;
  promptCount: number;
  color: string;
  order: number;
}

const categories: Category[] = [
  { id: 1, name: "Business", promptCount: 156, color: "#465fff", order: 1 },
  { id: 2, name: "Creative Writing", promptCount: 89, color: "#12b76a", order: 2 },
  { id: 3, name: "Programming", promptCount: 234, color: "#f79009", order: 3 },
  { id: 4, name: "Marketing", promptCount: 67, color: "#f04438", order: 4 },
  { id: 5, name: "Food & Cooking", promptCount: 45, color: "#7a5af8", order: 5 },
  { id: 6, name: "Health & Fitness", promptCount: 78, color: "#ee46bc", order: 6 },
];

export default function CategoriesOverview() {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] lg:p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90">
          Categories Overview
        </h3>
        <button className="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-600">
          <PlusIcon className="w-4 h-4" />
          Add Category
        </button>
      </div>

      <div className="space-y-4">
        {categories.map((category) => (
          <div
            key={category.id}
            className="flex items-center justify-between p-4 rounded-xl border border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-white/[0.02] transition-colors"
          >
            <div className="flex items-center gap-3">
              <div
                className="flex items-center justify-center w-10 h-10 rounded-lg"
                style={{ backgroundColor: `${category.color}20` }}
              >
                <FolderIcon
                  className="w-5 h-5"
                  style={{ color: category.color }}
                />
              </div>
              <div>
                <h4 className="font-medium text-gray-800 dark:text-white/90">
                  {category.name}
                </h4>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {category.promptCount} prompts
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 dark:text-gray-400">
                #{category.order}
              </span>
              <button className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                <MoreDotIcon className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-800">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500 dark:text-gray-400">
            Total Categories
          </span>
          <span className="font-medium text-gray-800 dark:text-white/90">
            {categories.length}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm mt-1">
          <span className="text-gray-500 dark:text-gray-400">
            Total Prompts
          </span>
          <span className="font-medium text-gray-800 dark:text-white/90">
            {categories.reduce((sum, cat) => sum + cat.promptCount, 0)}
          </span>
        </div>
      </div>
    </div>
  );
}
