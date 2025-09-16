"use client";
import React from "react";
import Label from "./Label";
import Input from "./input/InputField";
import TextArea from "./input/TextArea";
import Select from "./input/Select";
import { ChevronDownIcon } from "@/icons";

interface FormFieldProps {
  label: string;
  name: string;
  type?: "text" | "email" | "password" | "number" | "url" | "textarea" | "select";
  placeholder?: string;
  value?: string | number;
  defaultValue?: string | number;
  onChange?: (value: string | number) => void;
  onSelectChange?: (value: string) => void;
  options?: { value: string; label: string }[];
  rows?: number;
  required?: boolean;
  error?: string;
  className?: string;
  disabled?: boolean;
  min?: number;
  max?: number;
}

export default function FormField({
  label,
  name,
  type = "text",
  placeholder,
  value,
  defaultValue,
  onChange,
  onSelectChange,
  options = [],
  rows = 3,
  required = false,
  error,
  className = "",
  disabled = false,
  min,
  max,
}: FormFieldProps) {
  const hasError = !!error;
  const errorClasses = hasError ? "border-error-500" : "";

  const renderField = () => {
    switch (type) {
      case "textarea":
        return (
          <TextArea
            placeholder={placeholder}
            rows={rows}
            value={value as string}
            onChange={(val) => onChange?.(val)}
            className={`${errorClasses} ${className}`}
            disabled={disabled}
          />
        );

      case "select":
        return (
          <div className="relative">
            <Select
              options={options}
              placeholder={placeholder}
              value={value as string}
              onChange={onSelectChange || (() => {})}
              className={`${errorClasses} ${className}`}
            />
            <span className="absolute text-gray-500 -translate-y-1/2 pointer-events-none right-3 top-1/2 dark:text-gray-400">
              <ChevronDownIcon />
            </span>
          </div>
        );

      default:
        return (
          <Input
            id={name}
            type={type}
            placeholder={placeholder}
            defaultValue={defaultValue || value}
            onChange={(e) => onChange?.(e.target.value)}
            className={`${errorClasses} ${className}`}
            disabled={disabled}
            min={min?.toString()}
            max={max?.toString()}
          />
        );
    }
  };

  return (
    <div>
      <Label htmlFor={name}>
        {label}
        {required && <span className="text-error-500 ml-1">*</span>}
      </Label>
      {renderField()}
      {hasError && (
        <p className="text-error-500 text-sm mt-1">{error}</p>
      )}
    </div>
  );
}
