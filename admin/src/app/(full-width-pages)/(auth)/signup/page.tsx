import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign Up | RoyalPrompts Admin",
  description: "Create your RoyalPrompts Admin account",
};

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen">
      {/* Left side - Image/Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-brand-500 to-brand-600 items-center justify-center">
        <div className="text-center text-white">
          <h1 className="text-4xl font-bold mb-4">RoyalPrompts</h1>
          <p className="text-xl opacity-90">Admin Dashboard</p>
          <p className="mt-4 opacity-75">Create your admin account</p>
        </div>
      </div>
      
      {/* Right side - Sign Up Form */}
      <div className="flex flex-1 items-center justify-center px-4 sm:px-6 lg:px-8">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              Create Account
            </h2>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Sign up for your admin account
            </p>
          </div>
          
          <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg dark:bg-yellow-900/20 dark:border-yellow-800 dark:text-yellow-400">
            <p className="text-sm">
              Sign up is currently disabled. Please contact the administrator for access.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
