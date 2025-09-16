"use client";
import React from "react";
import Image from "next/image";
import { UserCircleIcon, TrashBinIcon, PencilIcon } from "@/icons";
import Badge from "../ui/badge/Badge";

interface User {
  id: number;
  name: string;
  email: string;
  favoritesCount: number;
  lastActive: string;
  isActive: boolean;
  avatar?: string;
}

const users: User[] = [
  {
    id: 1,
    name: "John Doe",
    email: "john@example.com",
    favoritesCount: 23,
    lastActive: "2 hours ago",
    isActive: true,
    avatar: "/images/user/user-17.jpg",
  },
  {
    id: 2,
    name: "Jane Smith",
    email: "jane@example.com",
    favoritesCount: 15,
    lastActive: "1 day ago",
    isActive: true,
    avatar: "/images/user/user-18.jpg",
  },
  {
    id: 3,
    name: "Mike Johnson",
    email: "mike@example.com",
    favoritesCount: 8,
    lastActive: "3 days ago",
    isActive: false,
    avatar: "/images/user/user-19.jpg",
  },
  {
    id: 4,
    name: "Sarah Wilson",
    email: "sarah@example.com",
    favoritesCount: 31,
    lastActive: "5 hours ago",
    isActive: true,
    avatar: "/images/user/user-20.jpg",
  },
  {
    id: 5,
    name: "Anonymous User",
    email: "anonymous@example.com",
    favoritesCount: 5,
    lastActive: "1 week ago",
    isActive: false,
  },
];

export default function UserActivity() {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-white/[0.03]">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-semibold text-gray-800 dark:text-white/90">
            Recent User Activity
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Latest user interactions and favorites
          </p>
        </div>
        <button className="text-sm text-brand-500 hover:text-brand-600 dark:text-brand-400 font-medium">
          View All
        </button>
      </div>

      <div className="space-y-4">
        {users.map((user) => (
          <div
            key={user.id}
            className="flex items-center justify-between p-4 rounded-xl border border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-white/[0.02] transition-all duration-200"
          >
            <div className="flex items-center gap-3">
              <div className="relative">
                {user.avatar ? (
                  <Image
                    src={user.avatar}
                    alt={user.name}
                    width={48}
                    height={48}
                    className="rounded-full object-cover"
                  />
                ) : (
                  <UserCircleIcon className="w-12 h-12 text-gray-400" />
                )}
                <div
                  className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white ${
                    user.isActive ? "bg-success-500" : "bg-gray-400"
                  }`}
                />
              </div>
              <div className="min-w-0 flex-1">
                <h4 className="font-medium text-gray-800 dark:text-white/90 truncate">
                  {user.name}
                </h4>
                <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                  {user.email}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <Badge color="info" size="sm">
                    {user.favoritesCount} favorites
                  </Badge>
                  <span className="text-xs text-gray-400">
                    {user.lastActive}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
                <PencilIcon className="w-4 h-4" />
              </button>
              <button className="p-2 text-gray-400 hover:text-error-500 dark:hover:text-error-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
                <TrashBinIcon className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-800">
        <div className="grid grid-cols-2 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-gray-800 dark:text-white/90">
              {users.filter(u => u.isActive).length}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Active Users
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-800 dark:text-white/90">
              {users.reduce((sum, user) => sum + user.favoritesCount, 0)}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Total Favorites
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
