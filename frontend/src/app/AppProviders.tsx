import type { ReactNode } from "react";

import {
  PersistQueryClientProvider,
  type PersistQueryClientProviderProps,
} from "@tanstack/react-query-persist-client";

import {
  appQueryClient,
  shouldDehydrateQuery,
  queryPersister,
} from "@/shared/lib/query-client";

type AppProvidersProps = {
  children: ReactNode;
};

const persistOptions: PersistQueryClientProviderProps["persistOptions"] = {
  persister: queryPersister,
  dehydrateOptions: {
    shouldDehydrateQuery,
  },
};

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <PersistQueryClientProvider
      client={appQueryClient}
      persistOptions={persistOptions}
    >
      {children}
    </PersistQueryClientProvider>
  );
}
