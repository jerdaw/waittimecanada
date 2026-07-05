import { getRequestConfig } from "next-intl/server";

export default getRequestConfig(async () => {
  // Locale routing is handled at the app route level; request config defaults to English.
  const locale = "en";

  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});
