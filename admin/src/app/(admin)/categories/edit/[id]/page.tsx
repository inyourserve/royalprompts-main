"use client";
import React from "react";
import { useParams } from "next/navigation";
import ComponentCard from "@/components/common/ComponentCard";
import PageHeader from "@/components/common/PageHeader";
import EditCategoryForm from "@/components/royalprompts/EditCategoryForm";

export default function EditCategoryPage() {
  const params = useParams();
  const categoryId = params.id as string;

  return (
    <div className="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10">
      <PageHeader 
        title="Edit Category"
        description="Update category information and settings"
      />
      
      <div className="grid grid-cols-1 gap-6">
        <ComponentCard title="Edit Category">
          <EditCategoryForm categoryId={categoryId} />
        </ComponentCard>
      </div>
    </div>
  );
}
