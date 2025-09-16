import SignInForm from "@/components/auth/SignInForm";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign In | RoyalPrompts Admin",
  description: "Sign in to RoyalPrompts Admin Dashboard",
};

export default function SignInPage() {
  return (
    <div className="flex min-h-screen">
      {/* Left side - Image/Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-brand-500 to-brand-600 items-center justify-center">
        <div className="text-center text-white">
          <h1 className="text-4xl font-bold mb-4">RoyalPrompts</h1>
          <p className="text-xl opacity-90">Admin Dashboard</p>
          <p className="mt-4 opacity-75">Manage your prompts, categories, and users</p>
        </div>
      </div>
      
      {/* Right side - Sign In Form */}
      <div className="flex flex-1 items-center justify-center px-4 sm:px-6 lg:px-8">
        <SignInForm />
      </div>
    </div>
  );
}
