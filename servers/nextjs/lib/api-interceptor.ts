/**
 * API fetch wrapper that automatically handles authentication
 * and shows login popup on 401 responses
 */

let setShowAuthPopupGlobal: ((show: boolean) => void) | null = null;

export function registerAuthPopupHandler(handler: (show: boolean) => void) {
  setShowAuthPopupGlobal = handler;
}

export async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  // Get token from localStorage
  const token = localStorage.getItem("auth_token");

  // Add Authorization header if token exists
  const headers = new Headers(options.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  // Make the request
  const response = await fetch(url, {
    ...options,
    headers,
  });

  // If 401 Unauthorized or 403 Forbidden (not authenticated), show auth popup
  if (response.status === 401 || response.status === 403) {
    if (setShowAuthPopupGlobal) {
      setShowAuthPopupGlobal(true);
    }
    throw new Error("Authentication required");
  }

  return response;
}
