import type { Metadata } from "next";
import React from "react";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import PromptsTable from "@/components/royalprompts/PromptsTable";

export const metadata: Metadata = {
  title: "Prompts Management | RoyalPrompts Admin",
  description: "Manage all prompts in RoyalPrompts platform",
};

export default function PromptsPage() {
  return (
    <>
      <PageBreadcrumb pageTitle="Prompts Management" />
      <PromptsTable />
    </>
  );
}
