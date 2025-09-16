"use client";
import React from "react";
import { useParams } from "next/navigation";
import ComponentCard from "@/components/common/ComponentCard";
import PageHeader from "@/components/common/PageHeader";
import EditPromptForm from "@/components/royalprompts/EditPromptForm";

export default function EditPromptPage() {
  const params = useParams();
  const promptId = params.id as string;

  return (
    <div className="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10">
      <PageHeader 
        title="Edit Prompt"
        description="Update prompt information and settings"
      />
      
      <div className="grid grid-cols-1 gap-6">
        <ComponentCard title="Edit Prompt">
          <EditPromptForm promptId={promptId} />
        </ComponentCard>
      </div>
    </div>
  );
}
