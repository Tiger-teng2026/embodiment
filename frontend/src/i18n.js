import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import zh from "./locales/zh.json";
import en from "./locales/en.json";

const STORAGE_KEY = "embodiment_lang";
const saved = localStorage.getItem(STORAGE_KEY);

i18n.use(initReactI18next).init({
  resources: {
    zh: { translation: zh },
    en: { translation: en },
  },
  lng: saved === "en" ? "en" : "zh",
  fallbackLng: "zh",
  interpolation: { escapeValue: false },
});

document.documentElement.lang = i18n.language === "en" ? "en" : "zh-CN";

export function setLanguage(lng) {
  const next = lng === "en" ? "en" : "zh";
  i18n.changeLanguage(next);
  localStorage.setItem(STORAGE_KEY, next);
  document.documentElement.lang = next === "en" ? "en" : "zh-CN";
}

export default i18n;
