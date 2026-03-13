import { useLocale, useAppIntl } from "@/shared/lib/i18n";

export function LanguageSwitcher() {
  const intl = useAppIntl();
  const { locale, setLocale } = useLocale();

  return (
    <select
      aria-label={intl.formatMessage({ id: "common.language" })}
      value={locale}
      onChange={(event) => setLocale(event.target.value as "en" | "ru")}
    >
      <option value="en">{intl.formatMessage({ id: "common.english" })}</option>
      <option value="ru">{intl.formatMessage({ id: "common.russian" })}</option>
    </select>
  );
}
