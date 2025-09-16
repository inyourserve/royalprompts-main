import type { Metadata } from "next";
import React from "react";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import CategoriesTable from "@/components/royalprompts/CategoriesTable";

export const metadata: Metadata = {
  title: "Categories Management - RoyalPrompts Admin",
  description: "Manage categories in the RoyalPrompts system",
};

export default function CategoriesPage() {
  return (
    <div className="space-y-6">
      <PageBreadcrumb pageTitle="Categories Management" />
      <CategoriesTable />
    </div>
  );
}
