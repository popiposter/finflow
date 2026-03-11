import { del, get, set } from "idb-keyval";
import { QueryClient } from "@tanstack/react-query";
import { createAsyncStoragePersister } from "@tanstack/query-async-storage-persister";
import type { Query } from "@tanstack/react-query";

const QUERY_CACHE_KEY = "finflow-offline-query-cache";

const asyncStorage = {
  async getItem(key: string) {
    const result = await get<string | null>(key);
    return result ?? null;
  },
  async setItem(key: string, value: string) {
    await set(key, value);
  },
  async removeItem(key: string) {
    await del(key);
  },
};

export const appQueryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      gcTime: 1000 * 60 * 60 * 24,
      retry(failureCount, error) {
        if (typeof navigator !== "undefined" && !navigator.onLine) {
          return false;
        }

        if (error instanceof Error && "status" in error) {
          const status = Number((error as { status: number }).status);
          if (status >= 400 && status < 500) {
            return false;
          }
        }

        return failureCount < 1;
      },
    },
    mutations: {
      retry: false,
    },
  },
});

export const queryPersister = createAsyncStoragePersister({
  storage: asyncStorage,
  key: QUERY_CACHE_KEY,
});

export function shouldDehydrateQuery(query: Query) {
  return query.state.status === "success" && query.queryKey[0] !== "auth";
}

export async function clearPersistedQueries() {
  await asyncStorage.removeItem(QUERY_CACHE_KEY);
}
