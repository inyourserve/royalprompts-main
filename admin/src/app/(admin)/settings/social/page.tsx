import type { Metadata } from "next";
import React from "react";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import SocialLinksForm from "@/components/royalprompts/SocialLinksForm";

export const metadata: Metadata = {
  title: "Social Links - RoyalPrompts Admin",
  description: "Configure social media links and channels",
};

export default function SocialLinksPage() {
  return (
    <div className="space-y-6">
      <PageBreadcrumb pageTitle="Social Links" />
      <SocialLinksForm />
    </div>
  );
}
