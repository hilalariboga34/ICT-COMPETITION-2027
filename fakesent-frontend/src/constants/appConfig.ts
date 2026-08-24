// Marka/isim/logo ileride değişebilir
// Kod içinde hiçbir yerde "FakeSent" string'i doğrudan yazılmaz, hep buradan okunur.
export const APP_CONFIG = {
  name: "FakeSent",
  shortName: "FS",
  version: "0.1.0-mvp",
  theme: {
    accent: "cyan", // marka rengi netleşene kadar nötr varsayılan
  },
} as const;