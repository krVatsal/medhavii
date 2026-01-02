"use client";

import { AuthPopup } from "./AuthPopup";
import { useAuth } from "@/lib/auth-context";
import { ReactNode, useEffect } from "react";
import { registerAuthPopupHandler } from "@/lib/api-interceptor";

export function AuthWrapper({ children }: { children: ReactNode }) {
  const { showAuthPopup, setShowAuthPopup, login } = useAuth();

  // Register the auth popup handler for API interceptor
  useEffect(() => {
    registerAuthPopupHandler(setShowAuthPopup);
  }, [setShowAuthPopup]);

  const handleLoginSuccess = (userData: any, token: string) => {
    login(userData, token);
    setShowAuthPopup(false);
  };

  return (
    <>
      {children}
      <AuthPopup
        isOpen={showAuthPopup}
        onClose={() => setShowAuthPopup(false)}
        onLoginSuccess={(userData) => {
          const token = localStorage.getItem("auth_token");
          if (token) {
            handleLoginSuccess(userData, token);
          }
        }}
      />
    </>
  );
}
