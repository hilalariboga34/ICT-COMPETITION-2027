// Marka/isim/logo merkezi olarak buradan yönetilir.
// Kod içinde marka adı doğrudan yazılmaz, APP_CONFIG üzerinden okunur.

export const APP_CONFIG = {
  name: "PersonaLive",
  shortName: "PL",
  version: "0.1.0-mvp",
  theme: {
    accent: "cyan", // marka rengi netleşene kadar nötr varsayılan
  },
} as const;
