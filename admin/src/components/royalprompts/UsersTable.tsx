"use client";
import React, { useState, useEffect } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableRow,
} from "../ui/table";
import Badge from "../ui/badge/Badge";
import Button from "../ui/button/Button";
import { TrashBinIcon, UserCircleIcon } from "@/icons";
import ComponentCard from "../common/ComponentCard";
import { usersApi } from "@/services";
import { DeviceUser } from "@/services/users-api";
import Alert from "../ui/alert/Alert";

// Helper function to format time ago
const formatTimeAgo = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (diffInSeconds < 60) return `${diffInSeconds} seconds ago`;
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`;
  return `${Math.floor(diffInSeconds / 2592000)} months ago`;
};

// Helper function to get device icon
const getDeviceIcon = (deviceType: string): string => {
  switch (deviceType) {
    case 'android': return '🤖';
    case 'ios': return '🍎';
    case 'web': return '🌐';
    default: return '📱';
  }
};

export default function UsersTable() {
  const [users, setUsers] = useState<DeviceUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [deviceTypeFilter, setDeviceTypeFilter] = useState("All");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [limit] = useState(20);

  // Load users on component mount and when filters change
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const isActive = statusFilter === "Active" ? true : 
                        statusFilter === "Inactive" ? false : undefined;
        const isBlocked = statusFilter === "Banned" ? true : undefined;
        const deviceType = deviceTypeFilter === "All" ? undefined : deviceTypeFilter;
        
        const response = await usersApi.getUsers(
          page,
          limit,
          searchTerm || undefined,
          deviceType,
          isActive,
          isBlocked
        );
        
        setUsers(response.items);
        setTotal(response.total);
      } catch (err) {
        console.error("Failed to fetch users:", err);
        setError(err instanceof Error ? err.message : "Failed to load users");
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, [page, searchTerm, statusFilter, deviceTypeFilter]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [searchTerm, statusFilter, deviceTypeFilter]);

  const getStatusBadge = (user: DeviceUser) => {
    if (user.is_blocked) {
      return <Badge color="error" size="sm">Blocked</Badge>;
    } else if (user.is_active) {
      return <Badge color="success" size="sm">Active</Badge>;
    } else {
      return <Badge color="warning" size="sm">Inactive</Badge>;
    }
  };

  const handleBlockUser = async (userId: string) => {
    try {
      await usersApi.blockUser(userId);
      // Refresh the users list
      const response = await usersApi.getUsers(page, limit);
      setUsers(response.items);
    } catch (err) {
      console.error("Failed to block user:", err);
      setError(err instanceof Error ? err.message : "Failed to block user");
    }
  };

  const handleUnblockUser = async (userId: string) => {
    try {
      await usersApi.unblockUser(userId);
      // Refresh the users list
      const response = await usersApi.getUsers(page, limit);
      setUsers(response.items);
    } catch (err) {
      console.error("Failed to unblock user:", err);
      setError(err instanceof Error ? err.message : "Failed to unblock user");
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm("Are you sure you want to delete this user? This action cannot be undone.")) {
      return;
    }
    
    try {
      await usersApi.deleteUser(userId);
      // Refresh the users list
      const response = await usersApi.getUsers(page, limit);
      setUsers(response.items);
      setTotal(response.total);
    } catch (err) {
      console.error("Failed to delete user:", err);
      setError(err instanceof Error ? err.message : "Failed to delete user");
    }
  };

  if (loading && users.length === 0) {
    return (
      <ComponentCard
        title="All Users"
        desc="Manage device users and permissions"
      >
        <div className="animate-pulse space-y-4">
          <div className="h-10 bg-gray-200 rounded dark:bg-gray-700"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, index) => (
              <div key={index} className="h-16 bg-gray-200 rounded dark:bg-gray-700"></div>
            ))}
          </div>
        </div>
      </ComponentCard>
    );
  }

  return (
    <ComponentCard
      title="All Users"
      desc="Manage device users and permissions"
    >
      {error && (
        <Alert
          variant="error"
          title="Error"
          message={error}
        />
      )}

      {/* Search and Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
        <div className="relative flex-1 max-w-md">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <UserCircleIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            placeholder="Search by device ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-brand-500 focus:border-brand-500 sm:text-sm dark:bg-gray-900 dark:border-gray-700 dark:text-white"
          />
        </div>

        <div className="flex items-center gap-3">
          <select
            value={deviceTypeFilter}
            onChange={(e) => setDeviceTypeFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-brand-500 focus:border-brand-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
          >
            <option value="All">All Devices</option>
            <option value="android">Android</option>
            <option value="ios">iOS</option>
            <option value="web">Web</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-brand-500 focus:border-brand-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
          >
            <option value="All">All Status</option>
            <option value="Active">Active</option>
            <option value="Inactive">Inactive</option>
            <option value="Banned">Blocked</option>
          </select>
       </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
        <div className="max-w-full overflow-x-auto">
          <div className="min-w-[1000px]">
            <Table>
              <TableHeader className="border-b border-gray-100 dark:border-gray-800">
                <TableRow className="bg-gray-50 dark:bg-gray-800">
                  <TableCell
                    isHeader
                    className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400"
                  >
                    Device
                  </TableCell>
                  <TableCell
                    isHeader
                    className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400"
                  >
                    Device ID
                  </TableCell>
                  <TableCell
                    isHeader
                    className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400"
                  >
                    Favorites
                  </TableCell>
                  <TableCell
                    isHeader
                    className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400"
                  >
                    Status
                  </TableCell>
                  <TableCell
                    isHeader
                    className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400"
                  >
                    Last Active
                  </TableCell>
                  <TableCell
                    isHeader
                    className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400"
                  >
                    First Seen
                  </TableCell>
                  <TableCell
                    isHeader
                    className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400"
                  >
                    Actions
                  </TableCell>
                </TableRow>
              </TableHeader>
              <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
                {users.map((user) => (
                  <TableRow key={user.id} className="bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800">
                    <TableCell className="px-5 py-4 sm:px-6 text-start">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 flex items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800">
                          <span className="text-lg">{getDeviceIcon(user.device_type)}</span>
                        </div>
                        <div>
                          <span className="block font-medium text-gray-800 text-theme-sm dark:text-white capitalize">
                            {user.device_type}
                          </span>
                          <span className="block text-gray-500 text-theme-xs dark:text-gray-400">
                            {user.device_model || 'Unknown Model'}
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="px-4 py-3 text-gray-500 text-theme-sm dark:text-gray-400 font-mono">
                      {user.device_id.substring(0, 8)}...
                    </TableCell>
                    <TableCell className="px-4 py-3 text-gray-500 text-theme-sm dark:text-gray-400">
                      {user.total_favorites}
                    </TableCell>
                    <TableCell className="px-4 py-3 text-start">
                      {getStatusBadge(user)}
                    </TableCell>
                    <TableCell className="px-4 py-3 text-gray-500 text-theme-sm dark:text-gray-400">
                      {formatTimeAgo(user.last_seen)}
                    </TableCell>
                    <TableCell className="px-4 py-3 text-gray-500 text-theme-sm dark:text-gray-400">
                      {new Date(user.first_seen).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="px-4 py-3 text-start">
                      <div className="flex items-center gap-2">
                        {user.is_blocked ? (
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => handleUnblockUser(user.id)}
                          >
                            Unblock
                          </Button>
                        ) : (
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => handleBlockUser(user.id)}
                          >
                            Block
                          </Button>
                        )}
                        <button 
                          className="p-1 text-gray-500 hover:text-error-500 dark:text-gray-400 dark:hover:text-error-400"
                          onClick={() => handleDeleteUser(user.id)}
                        >
                          <TrashBinIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="flex items-center justify-between pt-4">
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Showing {users.length} of {total} users
        </div>
        <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
          <span>Active: {users.filter(u => u.is_active && !u.is_blocked).length}</span>
          <span>Inactive: {users.filter(u => !u.is_active && !u.is_blocked).length}</span>
          <span>Blocked: {users.filter(u => u.is_blocked).length}</span>
        </div>
      </div>

      {/* Pagination */}
      {total > limit && (
        <div className="flex items-center justify-center gap-2 pt-4">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Page {page} of {Math.ceil(total / limit)}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= Math.ceil(total / limit)}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </ComponentCard>
  );
}
