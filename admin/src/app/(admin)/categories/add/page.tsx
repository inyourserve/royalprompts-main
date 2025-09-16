"use client";
import React from "react";
import ComponentCard from "@/components/common/ComponentCard";
import PageHeader from "@/components/common/PageHeader";
import AddCategoryForm from "@/components/royalprompts/AddCategoryForm";

export default function AddCategoryPage() {
  return (
    <div className="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10">
      <PageHeader 
        title="Add New Category"
        description="Create a new category for organizing prompts"
      />
      
      <div className="grid grid-cols-1 gap-6">
        <ComponentCard title="Add New Category">
          <AddCategoryForm />
        </ComponentCard>
      </div>
    </div>
  );
}
