// API_BASE_URL / WS_BASE_URL component içine hardcode edilmez, hep buradan okunur.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL ?? "";
export const DEMO_SESSION_ID = import.meta.env.VITE_DEMO_SESSION_ID ?? "";
export const USE_MOCK_PARTICIPANTS =
  import.meta.env.VITE_USE_MOCK_PARTICIPANTS === "true";