import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getCurrentUser,
  loginWithPassword,
  logoutCurrentSession,
  registerUser,
} from "@/shared/api/auth";
import type { LoginInput, RegisterInput, User } from "@/shared/api/types";
import { clearPersistedQueries } from "@/shared/lib/query-client";

export const sessionQueryKey = ["auth", "session"] as const;

export function useSessionQuery() {
  return useQuery({
    queryKey: sessionQueryKey,
    queryFn: getCurrentUser,
    retry: false,
    staleTime: 30_000,
  });
}

export function useLoginMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: LoginInput) => {
      await loginWithPassword(payload);
      return getCurrentUser();
    },
    onSuccess: (user) => {
      queryClient.setQueryData(sessionQueryKey, user);
    },
  });
}

export function useRegisterMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: RegisterInput) => {
      await registerUser(payload);
      await loginWithPassword({
        email: payload.email,
        password: payload.password,
      });
      return getCurrentUser();
    },
    onSuccess: (user) => {
      queryClient.setQueryData(sessionQueryKey, user);
    },
  });
}

export function useLogoutMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: logoutCurrentSession,
    onSuccess: async () => {
      queryClient.removeQueries();
      queryClient.clear();
      await clearPersistedQueries();
    },
  });
}

export function getInitials(user: User | undefined) {
  if (!user) {
    return "FF";
  }

  return user.email.slice(0, 2).toUpperCase();
}
