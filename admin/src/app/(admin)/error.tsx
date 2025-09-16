"use client";

import { useEffect } from "react";
import ComponentCard from "@/components/common/ComponentCard";
import Button from "@/components/ui/button/Button";
import Alert from "@/components/ui/alert/Alert";

export default function AdminError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error("Admin page error:", error);
  }, [error]);

  return (
    <div className="p-4 mx-auto max-w-(--breakpoint-2xl) md:p-6 bg-gray-50 dark:bg-gray-950 min-h-screen">
      <div className="space-y-6">
        <ComponentCard
          title="Page Error"
          desc="An error occurred while loading this page"
        >
          <div className="space-y-4">
            <Alert
              variant="error"
              title="Error Details"
              message={error.message || "An unexpected error occurred"}
              showLink={false}
            />
            
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button
                onClick={reset}
                className="inline-flex items-center justify-center"
              >
                Try again
              </Button>
              <Button
                variant="outline"
                onClick={() => window.location.href = "/dashboard"}
                className="inline-flex items-center justify-center"
              >
                Back to Dashboard
              </Button>
            </div>
          </div>
        </ComponentCard>
      </div>
    </div>
  );
}
