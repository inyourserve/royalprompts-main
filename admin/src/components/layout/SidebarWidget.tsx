import React from "react";
import { Globe } from "lucide-react";

export default function SidebarWidget() {
  return (
    <div className="mt-auto p-2">
      <div
        className={`
          mx-auto mb-10 w-full max-w-60 rounded-2xl bg-gray-50 px-4 py-5 text-center dark:bg-white/[0.03]`}
      >
        <div className="flex items-center justify-center mb-2">
          <Globe className="w-6 h-6 text-brand-500 mr-2" />
          <h3 className="font-semibold text-gray-900 dark:text-white">
            Bansohi Technology
          </h3>
        </div>
        <p className="mb-4 text-gray-500 text-theme-sm dark:text-gray-400">
          Developed by Bansohi Technology Private Limited — Your trusted partner for innovative software solutions and digital transformation.
        </p>
        <a
          href="mailto:contact@bansohitech.com"
          className="flex items-center justify-center p-3 font-medium text-white rounded-lg bg-brand-500 text-theme-sm hover:bg-brand-600"
        >
          Contact Us
        </a>
      </div>
    </div>
  );
}