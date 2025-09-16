"use client";
import React, { useState } from "react";
import Label from "./Label";
import Input from "./input/InputField";
import Button from "../ui/button/Button";
import Badge from "../ui/badge/Badge";

interface TagInputProps {
  label: string;
  tags: string[];
  onTagsChange: (tags: string[]) => void;
  placeholder?: string;
  required?: boolean;
  error?: string;
  maxTags?: number;
  className?: string;
}

export default function TagInput({
  label,
  tags,
  onTagsChange,
  placeholder = "Enter a tag and press Enter",
  required = false,
  error,
  maxTags,
  className = "",
}: TagInputProps) {
  const [tagInput, setTagInput] = useState("");

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      if (!maxTags || tags.length < maxTags) {
        onTagsChange([...tags, tagInput.trim()]);
        setTagInput("");
      }
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    onTagsChange(tags.filter(tag => tag !== tagToRemove));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddTag();
    }
  };

  const hasError = !!error;

  return (
    <div className={className}>
      <Label>
        {label}
        {required && <span className="text-error-500 ml-1">*</span>}
      </Label>
      
      <div className="flex gap-2 mb-3">
        <Input
          placeholder={placeholder}
          defaultValue={tagInput}
          onChange={(e) => setTagInput(e.target.value)}
          onKeyPress={handleKeyPress}
          className={hasError ? "border-error-500" : ""}
        />
        <Button
          onClick={handleAddTag}
          variant="outline"
          disabled={!tagInput.trim() || (maxTags ? tags.length >= maxTags : false)}
        >
          Add Tag
        </Button>
      </div>
      
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {tags.map((tag) => (
            <Badge key={tag} color="info">
              <span className="flex items-center gap-1">
                {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  className="ml-1 hover:text-white"
                >
                  ×
                </button>
              </span>
            </Badge>
          ))}
        </div>
      )}
      
      {hasError && (
        <p className="text-error-500 text-sm">{error}</p>
      )}
      
      {maxTags && (
        <p className="text-gray-500 text-sm mt-1">
          {tags.length}/{maxTags} tags
        </p>
      )}
    </div>
  );
}
