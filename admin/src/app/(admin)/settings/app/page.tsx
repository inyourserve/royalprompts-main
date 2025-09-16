import type { Metadata } from "next";
import React from "react";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import AppSettingsForm from "@/components/royalprompts/AppSettingsForm";

export const metadata: Metadata = {
  title: "App Settings - RoyalPrompts Admin",
  description: "Configure app settings and information",
};

export default function AppSettingsPage() {
  return (
    <div className="space-y-6">
      <PageBreadcrumb pageTitle="App Settings" />
      <AppSettingsForm />
    </div>
  );
}
