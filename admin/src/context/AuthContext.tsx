"use client";
import React, { createContext, useContext, useState, useEffect } from "react";
import { authApi, AuthContextType, AdminUser } from "@/services";

// Types are now imported from services

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AdminUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if user is logged in from localStorage on app load
    const initAuth = async () => {
      const savedToken = localStorage.getItem("royalprompts_token");
      const savedUser = localStorage.getItem("royalprompts_user");
      
      if (savedToken && savedUser) {
        try {
          setToken(savedToken);
          setUser(JSON.parse(savedUser));
          
          // Verify token is still valid by fetching current admin info
          try {
            const currentAdmin = await authApi.getCurrentAdmin();
            setUser(currentAdmin);
          } catch (error) {
            // Token is invalid, clear auth state
            console.error("Token validation failed:", error);
            clearAuthState();
          }
        } catch (error) {
          console.error("Error parsing saved auth data:", error);
          clearAuthState();
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const clearAuthState = () => {
    setUser(null);
    setToken(null);
    setError(null);
    localStorage.removeItem("royalprompts_user");
    localStorage.removeItem("royalprompts_token");
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await authApi.login({ email, password });
      
      // Store token and user data
      setToken(response.access_token);
      setUser(response.admin);
      
      localStorage.setItem("royalprompts_token", response.access_token);
      localStorage.setItem("royalprompts_user", JSON.stringify(response.admin));
      
      setLoading(false);
      return true;
    } catch (error) {
      console.error("Login failed:", error);
      setError(error instanceof Error ? error.message : "Login failed");
      setLoading(false);
      return false;
    }
  };

  const logout = () => {
    clearAuthState();
    // Redirect to login page after logout
    window.location.href = "/";
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user && !!token,
    token,
    login,
    logout,
    loading,
    error,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
