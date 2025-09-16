import type { Metadata } from "next";
import React from "react";
import { RoyalPromptsMetrics } from "@/components/royalprompts/RoyalPromptsMetrics";
import RecentPrompts from "@/components/royalprompts/RecentPrompts";
import PromptsChart from "@/components/royalprompts/PromptsChart";

export const metadata: Metadata = {
  title: "RoyalPrompts Admin Dashboard",
  description: "Admin dashboard for managing RoyalPrompts content and users",
};

export default function RoyalPromptsDashboard() {
  return (
    <div className="space-y-6">
      {/* Metrics Section */}
      <RoyalPromptsMetrics />
      
      {/* Charts Section */}
      <div className="col-span-12">
        <PromptsChart />
      </div>
      
      {/* Recent Prompts Section */}
      <div className="col-span-12">
        <RecentPrompts />
      </div>
    </div>
  );
}
