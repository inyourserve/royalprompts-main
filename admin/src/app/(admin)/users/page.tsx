import type { Metadata } from "next";
import React from "react";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import UsersTable from "@/components/royalprompts/UsersTable";

export const metadata: Metadata = {
  title: "Users Management - RoyalPrompts Admin",
  description: "Manage users in the RoyalPrompts system",
};

export default function UsersPage() {
  return (
    <div className="space-y-6">
      <PageBreadcrumb pageTitle="Users Management" />
      <UsersTable />
    </div>
  );
}
