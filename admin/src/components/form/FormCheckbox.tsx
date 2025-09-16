"use client";
import React from "react";
import Label from "./Label";

interface FormCheckboxProps {
  id: string;
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  description?: string;
  disabled?: boolean;
  className?: string;
}

export default function FormCheckbox({
  id,
  label,
  checked,
  onChange,
  description,
  disabled = false,
  className = "",
}: FormCheckboxProps) {
  return (
    <div className={`flex items-start gap-3 ${className}`}>
      <input
        type="checkbox"
        id={id}
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        disabled={disabled}
        className="w-4 h-4 text-brand-500 bg-gray-100 border-gray-300 rounded focus:ring-brand-500 dark:focus:ring-brand-500 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600 mt-1"
      />
      <div className="flex-1">
        <Label htmlFor={id} className="text-sm font-medium cursor-pointer">
          {label}
        </Label>
        {description && (
          <p className="text-gray-500 text-sm mt-1 dark:text-gray-400">
            {description}
          </p>
        )}
      </div>
    </div>
  );
}
