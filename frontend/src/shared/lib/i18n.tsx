import type { ReactNode } from "react";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { IntlProvider, useIntl } from "react-intl";

import { messages } from "@/shared/lib/messages";

export type SupportedLocale = "en" | "ru";

const DEFAULT_LOCALE: SupportedLocale = "en";
const STORAGE_KEY = "finflow.locale";

let currentLocale: SupportedLocale = DEFAULT_LOCALE;

type LocaleContextValue = {
  locale: SupportedLocale;
  setLocale: (locale: SupportedLocale) => void;
};

const LocaleContext = createContext<LocaleContextValue | null>(null);

export function AppIntlProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<SupportedLocale>(resolveInitialLocale);

  useEffect(() => {
    currentLocale = locale;
    if (typeof window !== "undefined" && hasStorage()) {
      window.localStorage.setItem(STORAGE_KEY, locale);
    }
    if (typeof document !== "undefined") {
      document.documentElement.lang = locale;
    }
  }, [locale]);

  const value = useMemo(() => ({ locale, setLocale }), [locale]);

  return (
    <LocaleContext.Provider value={value}>
      <IntlProvider
        defaultLocale={DEFAULT_LOCALE}
        locale={locale}
        messages={messages[locale]}
        onError={(error) => {
          if (error.code === "MISSING_TRANSLATION") {
            return;
          }
          throw error;
        }}
      >
        {children}
      </IntlProvider>
    </LocaleContext.Provider>
  );
}

export function useLocale() {
  const context = useContext(LocaleContext);

  if (!context) {
    throw new Error("useLocale must be used within AppIntlProvider");
  }

  return context;
}

export function useAppIntl() {
  return useIntl();
}

export function getCurrentLocale() {
  return currentLocale;
}

function resolveInitialLocale(): SupportedLocale {
  if (typeof window === "undefined") {
    return DEFAULT_LOCALE;
  }

  const stored = hasStorage() ? window.localStorage.getItem(STORAGE_KEY) : null;
  if (stored === "en" || stored === "ru") {
    currentLocale = stored;
    return stored;
  }

  const fromBrowser = window.navigator.language.toLowerCase().startsWith("ru")
    ? "ru"
    : DEFAULT_LOCALE;
  currentLocale = fromBrowser;
  return fromBrowser;
}

function hasStorage() {
  return (
    typeof window !== "undefined" &&
    typeof window.localStorage?.getItem === "function" &&
    typeof window.localStorage?.setItem === "function"
  );
}
