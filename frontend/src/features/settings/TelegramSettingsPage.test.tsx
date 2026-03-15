import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TelegramSettingsPage } from "@/features/settings/TelegramSettingsPage";
import { renderWithProviders } from "@/test/test-utils";

const getIntegrationStatus = vi.fn();
const listApiTokens = vi.fn();
const createApiToken = vi.fn();
const revokeApiToken = vi.fn();
const listTelegramLinks = vi.fn();
const disconnectTelegramLink = vi.fn();
const updateTelegramLink = vi.fn();
const listAccounts = vi.fn();

vi.mock("@/shared/api/auth", () => ({
  getIntegrationStatus: () => getIntegrationStatus(),
  listApiTokens: () => listApiTokens(),
  createApiToken: (payload: unknown) => createApiToken(payload),
  revokeApiToken: (tokenId: string) => revokeApiToken(tokenId),
  listTelegramLinks: () => listTelegramLinks(),
  disconnectTelegramLink: (linkId: string) => disconnectTelegramLink(linkId),
  updateTelegramLink: (linkId: string, payload: unknown) => updateTelegramLink(linkId, payload),
}));

vi.mock("@/shared/api/accounts", () => ({
  listAccounts: () => listAccounts(),
}));

describe("TelegramSettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getIntegrationStatus.mockResolvedValue({
      telegram: {
        enabled: true,
        bot_token_configured: true,
        webhook_secret_configured: true,
        commands: ["/connect <api_token> [account_id]", "/status", "/disconnect"],
      },
      ollama: {
        enabled: true,
        api_key_configured: true,
        base_url: "https://ollama.com/api",
        model: "gpt-oss:120b",
        min_confidence: 0.75,
      },
    });
    listAccounts.mockResolvedValue([
      {
        id: "acc-1",
        user_id: "user-1",
        name: "Main account",
        type: "checking",
        description: null,
        current_balance: "0.00",
        currency_code: "USD",
        is_active: true,
        opened_at: null,
        closed_at: null,
        created_at: "",
        updated_at: "",
      },
    ]);
    listApiTokens.mockResolvedValue([
      {
        id: "token-1",
        user_id: "user-1",
        name: "Telegram Bot",
        created_at: "2026-03-15T10:00:00Z",
        last_used_at: null,
        expires_at: "2027-03-15T10:00:00Z",
        is_revoked: false,
      },
    ]);
    listTelegramLinks.mockResolvedValue([
      {
        id: "link-1",
        user_id: "user-1",
        account_id: "acc-1",
        chat_id: 555001,
        telegram_user_id: 9001,
        username: "finflow_user",
        first_name: "Fin",
        is_active: true,
        last_seen_at: "2026-03-15T10:05:00Z",
        created_at: "2026-03-15T10:00:00Z",
        updated_at: "2026-03-15T10:05:00Z",
      },
    ]);
    createApiToken.mockResolvedValue({
      id: "token-2",
      user_id: "user-1",
      name: "Telegram Bot",
      created_at: "2026-03-15T10:00:00Z",
      last_used_at: null,
      expires_at: "2027-03-15T10:00:00Z",
      is_revoked: false,
      raw_token: "raw-token",
    });
    revokeApiToken.mockResolvedValue({
      id: "token-1",
      is_revoked: true,
    });
    disconnectTelegramLink.mockResolvedValue({
      id: "link-1",
      is_active: false,
    });
    updateTelegramLink.mockResolvedValue({
      id: "link-1",
      account_id: "acc-1",
    });
    vi.spyOn(window, "confirm").mockReturnValue(true);
  });

  it("shows linked chats and lets the user revoke and disconnect", async () => {
    const user = userEvent.setup();

    renderWithProviders(<TelegramSettingsPage />);

    await waitFor(() => expect(listApiTokens).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByText("Linked chats")).toBeInTheDocument());
    expect(screen.getByText("Linked chats")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Fin")).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: "Revoke" }));
    await waitFor(() => expect(revokeApiToken).toHaveBeenCalledWith("token-1"));

    await user.click(screen.getByRole("button", { name: "Disconnect" }));
    await waitFor(() => expect(disconnectTelegramLink).toHaveBeenCalledWith("link-1"));

    await user.selectOptions(screen.getByLabelText("Default account"), "acc-1");
    await waitFor(() =>
      expect(updateTelegramLink).toHaveBeenCalledWith("link-1", { account_id: "acc-1" }),
    );
  });
});
