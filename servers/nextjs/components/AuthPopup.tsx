"use client";

import { useState, useEffect } from "react";
import { GoogleLogin } from "@react-oauth/google";

interface AuthPopupProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (userData: any) => void;
}

export function AuthPopup({ isOpen, onClose, onLoginSuccess }: AuthPopupProps) {
  if (!isOpen) return null;

  const handleGoogleSuccess = async (credentialResponse: any) => {
    try {
      // Send ID token to backend
      const response = await fetch("/api/v1/ppt/auth/google/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          id_token: credentialResponse.credential,
        }),
      });

      if (!response.ok) {
        throw new Error("Authentication failed");
      }

      const data = await response.json();
      
      // Store token in localStorage
      localStorage.setItem("auth_token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));

      onLoginSuccess(data.user);
      onClose();
    } catch (error) {
      console.error("Login error:", error);
      alert("Failed to login. Please try again.");
    }
  };

  const handleGoogleError = () => {
    console.error("Google login failed");
    alert("Google login failed. Please try again.");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Sign in to continue</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        <p className="text-gray-600 mb-6">
          Sign in to access your generated presentations, images, videos, and more.
        </p>

        <div className="flex justify-center">
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleError}
            useOneTap={false}
            theme="outline"
            size="large"
            text="signin_with"
            shape="rectangular"
          />
        </div>

        <p className="text-xs text-gray-500 mt-6 text-center">
          By signing in, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </div>
  );
}
